"""
Vonage NCCO (Nexmo Call Control Object) response builders.

Vonage uses JSON NCCO arrays instead of Twilio's XML TwiML.
Language note: Vonage accepts "ar" for Arabic (NOT "ar-EG").
"""
from typing import Any

LANGUAGE = "ar"

# ── Agent dialogue ─────────────────────────────────────────────────────────────

GREETING_TEXT = (
    "السلام عليكم، "
    "كيف حالك عميلنا العزيز. "
    "أنا أتابع معك بخصوص المشكلة اللي كانت عندك. "
    "هل تم حلها؟ "
    "أرجو الرد بـ نعم أو لا."
)

NOT_UNDERSTOOD_TEXT = (
    "معلش يا فندم، مش فاهمت. "
    "ممكن تقولي تاني، هل المشكلة اتحلت؟ "
    "قول نعم لو اتحلت، أو لا لو لسه موجودة."
)

GOODBYE_RESOLVED_TEXT = (
    "تمام جدًا! "
    "سعيدين إن المشكلة اتحلت. "
    "شكرًا لوقتك يا فندم. "
    "يوم سعيد، مع السلامة."
)

GOODBYE_ESCALATE_TEXT = (
    "حسنًا يا فندم. "
    "هنبلغ فريق خدمة العملاء بخصوص مشكلتك، "
    "وهيتواصلوا معك في أقرب وقت. "
    "شكرًا لوقتك. مع السلامة."
)

NO_INPUT_TEXT = (
    "مفيش رد يا فندم. "
    "هنحاول نتواصل معك تاني لاحقًا. "
    "مع السلامة."
)


# ── NCCO builders ──────────────────────────────────────────────────────────────

def build_greeting_ncco(recording_webhook_url: str) -> list[dict[str, Any]]:
    """
    Initial NCCO: plays the greeting question and records customer's Arabic speech.
    Vonage POSTs the recording result to `recording_webhook_url`.
    """
    return [
        {
            "action": "talk",
            "text": GREETING_TEXT,
            "language": LANGUAGE,
            "bargeIn": True,
        },
        {
            "action": "record",
            "eventUrl": [recording_webhook_url],
            "eventMethod": "POST",
            "endOnSilence": 2,
            "timeOut": 15,
            "beepStart": False,
            "format": "mp3",
        },
    ]


def build_retry_ncco(recording_webhook_url: str) -> list[dict[str, Any]]:
    """
    Retry NCCO: plays clarification prompt then records customer's speech again.
    Used when Whisper / classifier couldn't determine YES or NO.
    """
    return [
        {
            "action": "talk",
            "text": NOT_UNDERSTOOD_TEXT,
            "language": LANGUAGE,
            "bargeIn": True,
        },
        {
            "action": "record",
            "eventUrl": [recording_webhook_url],
            "eventMethod": "POST",
            "endOnSilence": 2,
            "timeOut": 15,
            "beepStart": False,
            "format": "mp3",
        },
    ]


def build_resolved_ncco() -> list[dict[str, Any]]:
    """
    Final NCCO for the YES branch:
    Confirms the issue is resolved, updates DB to RESOLVED, thanks customer.
    """
    return [
        {
            "action": "talk",
            "text": GOODBYE_RESOLVED_TEXT,
            "language": LANGUAGE,
        }
    ]


def build_escalate_ncco() -> list[dict[str, Any]]:
    """
    Final NCCO for the NO branch:
    Tells customer that call center will follow up → DB marks NEEDS_HUMAN.
    """
    return [
        {
            "action": "talk",
            "text": GOODBYE_ESCALATE_TEXT,
            "language": LANGUAGE,
        }
    ]


def build_no_input_ncco() -> list[dict[str, Any]]:
    """NCCO played when the customer didn't speak at all (timeout)."""
    return [
        {
            "action": "talk",
            "text": NO_INPUT_TEXT,
            "language": LANGUAGE,
        }
    ]
