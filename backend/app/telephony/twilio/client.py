"""
Twilio REST client wrapper.

Provides a single, lazily-initialized Twilio Client instance built from
app settings, so the rest of the telephony module never touches
credentials or the twilio SDK directly.
"""
from functools import lru_cache
from twilio.rest import Client
from app.core.config import settings
from app.core.logging import logger


@lru_cache(maxsize=1)
def get_twilio_client() -> Client:
    """
    Returns a cached Twilio REST client built from env-configured credentials.

    Cached (not recreated per call) because constructing the client
    performs no network I/O but we don't want scattered instantiation
    across the codebase.
    """
    if not settings.TWILIO_ACCOUNT_SID or not settings.TWILIO_AUTH_TOKEN:
        raise RuntimeError(
            "Twilio credentials are missing. Set TWILIO_ACCOUNT_SID and "
            "TWILIO_AUTH_TOKEN in your .env file."
        )

    logger.info("Initializing Twilio client for account %s...", settings.TWILIO_ACCOUNT_SID[:8])
    return Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)


def get_from_number() -> str:
    """Returns the configured Twilio outbound caller ID number."""
    if not settings.TWILIO_PHONE_NUMBER:
        raise RuntimeError("TWILIO_PHONE_NUMBER is not set in your .env file.")
    return settings.TWILIO_PHONE_NUMBER
