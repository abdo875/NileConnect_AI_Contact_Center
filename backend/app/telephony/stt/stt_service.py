"""
Speech-to-Text (STT) Service entry point.

Exports WhisperSTTService for transcribing audio to Arabic text.
"""
from app.telephony.stt.whisper_service import WhisperSTTService, get_whisper_service

__all__ = ["WhisperSTTService", "get_whisper_service"]
 