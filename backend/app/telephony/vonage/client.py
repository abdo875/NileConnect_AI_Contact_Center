"""
Vonage REST client — cached singleton.

The private key is loaded from the FILE PATH stored in VONAGE_PRIVATE_KEY_PATH.
The key content is never stored in an environment variable or in code — only
the path to the key file is configured.
"""
from functools import lru_cache
from pathlib import Path

from vonage import Auth, Vonage

from app.core.config import settings
from app.core.logging import logger


@lru_cache(maxsize=1)
def get_vonage_client() -> Vonage:
    """
    Returns a cached Vonage client built from env-configured credentials.

    Raises RuntimeError if VONAGE_APPLICATION_ID or VONAGE_PRIVATE_KEY_PATH
    are missing or the key file does not exist.
    """
    if not settings.VONAGE_APPLICATION_ID:
        raise RuntimeError(
            "VONAGE_APPLICATION_ID is not set. Add it to your .env file."
        )
    if not settings.VONAGE_PRIVATE_KEY_PATH:
        raise RuntimeError(
            "VONAGE_PRIVATE_KEY_PATH is not set. Add the path to your .env file."
        )

    key_path = Path(settings.VONAGE_PRIVATE_KEY_PATH)
    if not key_path.is_absolute():
        # Resolve relative to the backend/ directory
        backend_root = Path(__file__).resolve().parent.parent.parent.parent
        key_path = (backend_root / key_path).resolve()

    if not key_path.exists():
        raise RuntimeError(
            f"Vonage private key file not found at: {key_path}\n"
            "Check VONAGE_PRIVATE_KEY_PATH in your .env file."
        )

    logger.info(
        "Initialising Vonage client (app_id=%s, key=%s)",
        settings.VONAGE_APPLICATION_ID[:8] + "...",
        key_path,
    )

    return Vonage(
        Auth(
            application_id=settings.VONAGE_APPLICATION_ID,
            private_key=str(key_path),
        )
    )


def get_from_number() -> str:
    """Returns the fixed outbound caller number from config."""
    if not settings.VONAGE_FROM_NUMBER:
        raise RuntimeError("VONAGE_FROM_NUMBER is not set in your .env file.")
    return settings.VONAGE_FROM_NUMBER


def get_to_number() -> str:
    """Returns the fixed destination number from config."""
    if not settings.VONAGE_TO_NUMBER:
        raise RuntimeError("VONAGE_TO_NUMBER is not set in your .env file.")
    return settings.VONAGE_TO_NUMBER
