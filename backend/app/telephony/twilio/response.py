"""
TwiML response builders.

Each function returns a ready-to-send TwiML (XML) string. FastAPI webhook
routes should return these directly with media_type="application/xml".

Keeping all TwiML construction here (rather than inline in webhook routes)
means the call script/wording lives in exactly one place.
"""
from twilio.twiml.voice_response import VoiceResponse, Gather

# Twilio's Arabic (Egypt) voice + language code.
# "Polly.Zeina" is Twilio's standard Arabic neural voice.
VOICE = "Polly.Zeina"
LANGUAGE = "ar-EG"

GREETING_TEXT = "أهلاً بيك، معاك نايل كونكت. عايزين نتأكد إن المشكلة اللي كانت عندك اتحلت. لو اتحلت قول أيوه، ولو لسه موجودة قول لأ."
NOT_UNDERSTOOD_TEXT = "معلش، ممكن تعيد تاني، اتحلت المشكلة ولا لأ؟"
GOODBYE_RESOLVED_TEXT = "تمام جدًا، شكرًا لوقتك. يوم سعيد."
GOODBYE_ESCALATE_TEXT = "تمام، هنبعت حد من فريقنا يتواصل معاك تاني في أقرب وقت. شكرًا لوقتك."
NO_ANSWER_TEXT = "مفيش حد رد، هنحاول نتصل تاني لاحقًا."


def build_greeting_response(speech_webhook_url: str) -> str:
    """
    First TwiML sent when the customer answers: plays the greeting/question
    and gathers their spoken YES/NO reply. Twilio POSTs the result to
    speech_webhook_url.
    """
    response = VoiceResponse()
    gather = Gather(
        input="speech",
        language=LANGUAGE,
        action=speech_webhook_url,
        method="POST",
        speech_timeout="auto",
    )
    gather.say(GREETING_TEXT, voice=VOICE, language=LANGUAGE)
    response.append(gather)

    # If Gather times out with no speech at all, Twilio falls through to here.
    response.say(NO_ANSWER_TEXT, voice=VOICE, language=LANGUAGE)
    response.hangup()
    return str(response)


def build_retry_response(speech_webhook_url: str) -> str:
    """
    Used when speech was captured but the classifier couldn't confidently
    determine YES/NO. Asks the customer to repeat once.
    """
    response = VoiceResponse()
    gather = Gather(
        input="speech",
        language=LANGUAGE,
        action=speech_webhook_url,
        method="POST",
        speech_timeout="auto",
    )
    gather.say(NOT_UNDERSTOOD_TEXT, voice=VOICE, language=LANGUAGE)
    response.append(gather)

    response.say(NO_ANSWER_TEXT, voice=VOICE, language=LANGUAGE)
    response.hangup()
    return str(response)


def build_resolved_response() -> str:
    """Final response for the YES branch: confirm and end the call."""
    response = VoiceResponse()
    response.say(GOODBYE_RESOLVED_TEXT, voice=VOICE, language=LANGUAGE)
    response.hangup()
    return str(response)


def build_escalate_response() -> str:
    """Final response for the NO branch: tell the customer a human will follow up, then end."""
    response = VoiceResponse()
    response.say(GOODBYE_ESCALATE_TEXT, voice=VOICE, language=LANGUAGE)
    response.hangup()
    return str(response)
