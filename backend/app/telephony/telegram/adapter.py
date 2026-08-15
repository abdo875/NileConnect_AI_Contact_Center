"""
Telegram Transport Adapter for NileConnect Voice-AI Architecture.

Acts as the transport bridge between the Telegram Bot API and the existing
application layer (STT, AI classifier, Call Flows, Database Models, and TTS).
Preserves existing call-flow logic, session tracking, and database models.
"""
from datetime import datetime, timezone
from typing import Dict, Any, Optional
from uuid import UUID, uuid4
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.constants import CallOutcome, CallType, CaseStatus, FollowupResult, FollowupStatus
from app.core.logging import logger
from app.models.ai_followup import AIFollowup
from app.models.call import Call
from app.models.case import Case
from app.models.customer import Customer
from app.repositories.call_repository import CallRepository
from app.repositories.case_repository import CaseRepository
from app.repositories.customer_repository import CustomerRepository
from app.repositories.followup_repository import FollowupRepository
from app.telephony.call_flows.no_flow import handle_no
from app.telephony.call_flows.unknown_flow import MAX_ATTEMPTS
from app.telephony.call_flows.yes_flow import handle_yes
from app.telephony.stt.arabic_classifier import classify_response
from app.telephony.stt.stt_service import get_stt_service
from app.telephony.tts.tts_service import get_tts_service
from app.telephony.telegram.client import get_telegram_client
from app.telephony.twilio.response import (
    GREETING_TEXT,
    NOT_UNDERSTOOD_TEXT,
    GOODBYE_RESOLVED_TEXT,
    GOODBYE_ESCALATE_TEXT,
)


class TelegramAdapter:
    """
    Session & Orchestration manager for Telegram transport.
    """
    def __init__(self, db: Session):
        self.db = db
        self.telegram_client = get_telegram_client()
        self.stt_service = get_stt_service()
        self.tts_service = get_tts_service()

        self.customer_repo = CustomerRepository(db)
        self.case_repo = CaseRepository(db)
        self.followup_repo = FollowupRepository(db)
        self.call_repo = CallRepository(db)

    def _get_or_create_session(
        self,
        chat_id: int | str,
        user_info: Optional[Dict[str, Any]] = None,
    ) -> tuple[AIFollowup, Call]:
        """
        Retrieves or establishes the active AIFollowup and Call records for this Telegram user.
        Preserves customer, case, and call flow tracking in PostgreSQL.
        """
        user_name = "Telegram User"
        if user_info:
            first = user_info.get("first_name", "")
            last = user_info.get("last_name", "")
            user_name = f"{first} {last}".strip() or user_info.get("username", "Telegram User")

        phone_num = f"TG_{chat_id}"

        # 1. Ensure Customer exists
        customer = self.customer_repo.get_by_phone(phone_num)
        if not customer:
            # Check if there is an existing demo customer we can link, or create a new one
            customer = Customer(
                name=user_name,
                phone=phone_num,
                notes=f"Telegram Chat ID: {chat_id}",
            )
            customer = self.customer_repo.create(customer)

        # 2. Find open follow-up or create one
        open_followups = self.followup_repo.get_all(
            customer_id=customer.id,
            status=FollowupStatus.IN_PROGRESS,
            limit=1,
        )
        if not open_followups:
            scheduled_followups = self.followup_repo.get_all(
                customer_id=customer.id,
                status=FollowupStatus.SCHEDULED,
                limit=1,
            )
            if scheduled_followups:
                followup = scheduled_followups[0]
            else:
                # Create a new Case & Followup
                case = Case(
                    customer_id=customer.id,
                    issue="متابعة جودة خدمة الإنترنت / الاتصال",
                    description="AI Outbound Follow-up via Telegram Transport",
                    status=CaseStatus.AI_FOLLOW_UP_SCHEDULED,
                )
                case = self.case_repo.create(case)

                followup = AIFollowup(
                    case_id=case.id,
                    customer_id=customer.id,
                    scheduled_at=datetime.now(timezone.utc),
                    status=FollowupStatus.IN_PROGRESS,
                    attempt_number=1,
                )
                followup = self.followup_repo.create(followup)
        else:
            followup = open_followups[0]

        # 3. Find or create Call row
        call = None
        if followup.call_id:
            call = self.call_repo.get_by_id(followup.call_id)

        if not call or call.outcome != CallOutcome.PENDING:
            call = Call(
                customer_id=customer.id,
                case_id=followup.case_id,
                call_type=CallType.OUTBOUND_AI,
                started_at=datetime.now(timezone.utc),
                outcome=CallOutcome.PENDING,
            )
            call = self.call_repo.create(call)
            followup.call_id = call.id
            followup.status = FollowupStatus.IN_PROGRESS
            self.followup_repo.update(followup)

        return followup, call

    def process_start_command(
        self,
        chat_id: int | str,
        user_info: Optional[Dict[str, Any]] = None,
        as_voice: bool = False,
    ) -> None:
        """
        Handles the /start command from Telegram user.
        Resets session state, sets up active follow-up & call records, and greets the user.
        """
        logger.info("[Telegram] Update received")
        logger.info("[Telegram] Message type: start")
        logger.info("[Telegram] Chat ID received: %s", chat_id)

        followup, call = self._get_or_create_session(chat_id, user_info)
        followup.attempt_number = 1
        self.followup_repo.update(followup)

        logger.info("[Telegram] Sending response")
        if as_voice:
            logger.info("[TTS] Generating audio (greeting)")
            audio_bytes = self.tts_service.synthesize_speech(GREETING_TEXT)
            logger.info("[TTS] Audio generated (size: %d bytes)", len(audio_bytes))
            self.telegram_client.send_voice(chat_id, audio_bytes, caption=GREETING_TEXT)
        else:
            self.telegram_client.send_message(chat_id, GREETING_TEXT)
        logger.info("[Telegram] Response sent successfully")

    def process_text_message(
        self,
        chat_id: int | str,
        text: str,
        user_info: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Handles incoming text messages from Telegram:
        Telegram -> Webhook -> AI Classifier -> Call Flows -> DB Update -> Telegram Text Response
        """
        logger.info("[Telegram] Update received")
        logger.info("[Telegram] Message type: text")
        logger.info("[Telegram] Chat ID received: %s", chat_id)

        if text.strip().startswith("/start"):
            self.process_start_command(chat_id, user_info, as_voice=False)
            return {"ok": True, "action": "start"}

        followup, call = self._get_or_create_session(chat_id, user_info)

        # AI Classification
        logger.info("[AI] Request sent: %r", text)
        result = classify_response(text)
        logger.info("[AI] Response received: %s", result.value)

        # Update Call transcript
        if call:
            current_transcript = call.transcript or ""
            call.transcript = (current_transcript + f"\nCustomer: {text}").strip()
            self.call_repo.update(call)

        response_text = self._execute_call_flow(followup, call, result)

        logger.info("[Telegram] Sending response")
        self.telegram_client.send_message(chat_id, response_text)
        logger.info("[Telegram] Response sent successfully")

        return {"ok": True, "result": result.value, "response": response_text}

    def process_voice_message(
        self,
        chat_id: int | str,
        file_id: str,
        user_info: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Handles incoming voice notes from Telegram:
        Telegram Voice -> Webhook -> Download Audio -> STT -> AI Classifier -> Call Flows -> DB Update -> TTS -> Telegram Voice Response
        """
        logger.info("[Telegram] Update received")
        logger.info("[Telegram] Message type: voice")
        logger.info("[Telegram] Chat ID received: %s", chat_id)

        # 1. Download voice audio from Telegram
        file_info = self.telegram_client.get_file(file_id)
        file_path = file_info.get("result", {}).get("file_path")
        if not file_path:
            logger.error("[Telegram] Could not obtain file_path for file_id: %s", file_id)
            err_msg = "عذرًا، حدث خطأ أثناء تحميل الرسالة الصوتية. برجاء المحاولة مرة أخرى."
            self.telegram_client.send_message(chat_id, err_msg)
            return {"ok": False, "error": "file_download_failed"}

        audio_bytes = self.telegram_client.download_file(file_path)

        # 2. Run STT
        transcribed_text = self.stt_service.transcribe_audio(
            audio_bytes=audio_bytes,
            filename=file_path.split("/")[-1] if "/" in file_path else "voice.oga",
        )

        followup, call = self._get_or_create_session(chat_id, user_info)

        # 3. AI / Classification
        logger.info("[AI] Request sent: %r", transcribed_text)
        result = classify_response(transcribed_text)
        logger.info("[AI] Response received: %s", result.value)

        # Update Call transcript
        if call:
            current_transcript = call.transcript or ""
            call.transcript = (current_transcript + f"\nCustomer (Voice): {transcribed_text}").strip()
            self.call_repo.update(call)

        # 4. Call Flows
        response_text = self._execute_call_flow(followup, call, result)

        # 5. Run TTS
        audio_response = self.tts_service.synthesize_speech(response_text)

        # 6. Send Voice back to Telegram
        logger.info("[Telegram] Sending response")
        if audio_response:
            self.telegram_client.send_voice(
                chat_id=chat_id,
                voice_bytes=audio_response,
                filename="response.mp3",
                caption=f"🗣️ {response_text}",
            )
        else:
            self.telegram_client.send_message(chat_id, response_text)
        logger.info("[Telegram] Response sent successfully")

        return {
            "ok": True,
            "transcription": transcribed_text,
            "result": result.value,
            "response": response_text,
        }

    def _execute_call_flow(
        self,
        followup: AIFollowup,
        call: Call,
        result: FollowupResult,
    ) -> str:
        """
        Executes the business logic / database updates from the existing call flow handlers.
        """
        if result == FollowupResult.YES:
            handle_yes(self.db, followup.id, call.id)
            return GOODBYE_RESOLVED_TEXT

        elif result == FollowupResult.NO:
            handle_no(self.db, followup.id, call.id)
            return GOODBYE_ESCALATE_TEXT

        else:
            # Unknown / ambiguous response
            attempt = followup.attempt_number or 1
            if attempt < MAX_ATTEMPTS:
                followup.attempt_number = attempt + 1
                self.followup_repo.update(followup)
                return NOT_UNDERSTOOD_TEXT
            else:
                # Out of retries: escalate to human agent
                handle_no(self.db, followup.id, call.id)
                return GOODBYE_ESCALATE_TEXT
