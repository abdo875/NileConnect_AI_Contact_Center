"""
Places an outbound AI follow-up call via Vonage.

KEY DESIGN:
  - FROM and TO numbers are ALWAYS fixed (env vars). Never from the customer.
  - The NCCO is embedded INLINE in create_call() using the `ncco` parameter.
    This means the call works WITHOUT needing Vonage to reach a public URL
    just to get the greeting — only the speech eventUrl needs to be reachable.
  - If PUBLIC_BASE_URL is localhost (dev mode), speech input still won't be
    transcribed back, but the call WILL ring and the greeting WILL play.
"""
from datetime import datetime, timezone
from uuid import UUID

from vonage_voice import CreateCallRequest, Phone, ToPhone
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.constants import CallOutcome, CallType, FollowupStatus
from app.core.logging import logger
from app.models.call import Call
from app.repositories.call_repository import CallRepository
from app.repositories.followup_repository import FollowupRepository
from app.telephony.vonage.client import get_from_number, get_to_number, get_vonage_client
from app.telephony.vonage.response import build_greeting_ncco


def place_vonage_followup_call(db: Session, followup_id: UUID) -> Call:
    """
    Immediately dials the fixed TO number for the given AIFollowup.

    Uses inline NCCO so the greeting plays as soon as the call is answered,
    without Vonage needing to make a separate HTTP request to answer_url.

    Returns the created Call row.
    Raises ValueError  — follow-up not found.
    Raises RuntimeError — missing Vonage credentials / numbers.
    """
    followup_repo = FollowupRepository(db)
    followup = followup_repo.get_by_id(followup_id)
    if not followup:
        raise ValueError(f"AIFollowup {followup_id} not found")

    # ── 1. Create the Call DB row BEFORE dialling ─────────────────────────────
    call = Call(
        customer_id=followup.customer_id,
        case_id=followup.case_id,
        call_type=CallType.OUTBOUND_AI,
        started_at=datetime.now(timezone.utc),
        outcome=CallOutcome.PENDING,
    )
    call_repo = CallRepository(db)
    created_call = call_repo.create(call)

    # ── 2. Link follow-up → call, mark IN_PROGRESS ───────────────────────────
    followup.call_id = created_call.id
    followup.status = FollowupStatus.IN_PROGRESS
    followup_repo.update(followup)

    # ── 3. Build NCCO inline ──────────────────────────────────────────────────
    # The recording eventUrl (for capturing the customer's audio) needs to be
    # reachable by Vonage. Use ngrok / public URL in PUBLIC_BASE_URL for that.
    recording_webhook_url = (
        f"{settings.PUBLIC_BASE_URL}/api/v1/vonage/recording"
        f"?followup_id={followup_id}&call_id={created_call.id}&attempt=1"
    )
    ncco = build_greeting_ncco(recording_webhook_url)

    # ── 4. Place the call with inline NCCO ───────────────────────────────────
    from_number = get_from_number()
    to_number   = get_to_number()

    logger.info(
        "Placing Vonage call: from=%s to=%s followup=%s call=%s",
        from_number, to_number, followup_id, created_call.id,
    )

    client = get_vonage_client()
    vonage_response = client.voice.create_call(
        CreateCallRequest(
            to=[ToPhone(number=to_number)],
            from_=Phone(number=from_number),
            ncco=ncco,          # ← inline NCCO — no answer_url needed
        )
    )

    logger.info(
        "Vonage call placed: followup=%s call=%s vonage_uuid=%s",
        followup_id,
        created_call.id,
        getattr(vonage_response, "uuid", "unknown"),
    )

    return created_call
