"""
Call flow branch: speech was captured but not confidently classified as
YES or NO.
 
Policy: give the customer one chance to repeat themselves. If it's still
unclear on the second attempt, fail safe by escalating to a human rather
than guessing — same outcome/logic as the NO flow.
"""
from app.telephony.call_flows.no_flow import handle_no
from app.telephony.twilio.response import build_retry_response
 
MAX_ATTEMPTS = 2
 
 
def handle_unknown(db, followup_id, call_id, speech_webhook_url: str, attempt: int = 1) -> str:
    if attempt < MAX_ATTEMPTS:
        return build_retry_response(speech_webhook_url)
 
    # Out of retries — fail safe to human escalation rather than guessing.
    return handle_no(db, followup_id, call_id)
 