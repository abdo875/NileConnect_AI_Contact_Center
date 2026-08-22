"""
Whisper Speech-to-Text (STT) Service.

Clean, dedicated STT module: Audio -> Whisper -> Arabic text.
Uses the Groq Whisper API (whisper-large-v3-turbo) via GROQ_API_KEY for
ultra-fast, highly accurate Arabic transcription (Egyptian Arabic & MSA).

Responsibilities:
  - Audio input validation and formatting
  - Whisper API transcription
  - Graceful error handling (returns empty string on failure, never crashes)
  - Zero business logic, zero database calls, zero telephony coupling
"""
import io
import os
from pathlib import Path
from typing import BinaryIO, Optional, Union

import groq
from app.core.config import settings
from app.core.logging import logger


class WhisperSTTService:
    """
    Dedicated Speech-to-Text service powered by Whisper.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        language: str = "ar",
    ):
        self.api_key = api_key or settings.GROQ_API_KEY
        self.model = model or settings.WHISPER_MODEL or "whisper-large-v3-turbo"
        self.language = language
        self._client: Optional[groq.Groq] = None

    @property
    def client(self) -> groq.Groq:
        """Lazily initialize and return the Groq client."""
        if self._client is None:
            if not self.api_key:
                raise RuntimeError(
                    "GROQ_API_KEY is not set. Please configure GROQ_API_KEY in your environment."
                )
            self._client = groq.Groq(api_key=self.api_key)
        return self._client

    def transcribe(
        self,
        audio_source: Union[bytes, str, Path, BinaryIO],
        prompt: Optional[str] = "مكالمة متابعة خدمة عملاء نايل كونكت",
    ) -> str:
        """
        Transcribes the given audio source to Arabic text.

        Parameters:
          audio_source: Audio file path, raw bytes, or a file-like binary stream.
          prompt: Optional Whisper context prompt to improve recognition accuracy.

        Returns:
          Clean Arabic transcript string, or "" if audio is empty or transcription fails.
        """
        if not audio_source:
            logger.warning("Whisper STT received empty audio source.")
            return ""

        try:
            file_payload = self._prepare_audio_file(audio_source)
            if file_payload is None:
                logger.warning("Failed to prepare audio payload for Whisper STT.")
                return ""

            logger.info("Transcribing audio with Whisper model: %s (lang=%s)", self.model, self.language)
            transcription = self.client.audio.transcriptions.create(
                file=file_payload,
                model=self.model,
                language=self.language,
                prompt=prompt,
            )

            text = getattr(transcription, "text", "") or ""
            transcript = text.strip()
            logger.info("Whisper transcription result: %r", transcript)
            return transcript

        except Exception as e:
            logger.exception("Whisper STT transcription failed: %s", e)
            return ""

    def _prepare_audio_file(
        self,
        audio_source: Union[bytes, str, Path, BinaryIO],
    ):
        """Prepares audio into a format suitable for the Groq client."""
        if isinstance(audio_source, bytes):
            if len(audio_source) == 0:
                return None
            return ("recording.mp3", io.BytesIO(audio_source))

        elif isinstance(audio_source, (str, Path)):
            path = Path(audio_source)
            if not path.exists() or path.stat().st_size == 0:
                logger.warning("Audio file does not exist or is empty: %s", path)
                return None
            filename = path.name or "recording.mp3"
            with open(path, "rb") as f:
                content = f.read()
            return (filename, io.BytesIO(content))

        elif hasattr(audio_source, "read"):
            data = audio_source.read()
            if not data:
                return None
            return ("recording.mp3", io.BytesIO(data))

        return None


# Global singleton instance
_whisper_service: Optional[WhisperSTTService] = None


def get_whisper_service() -> WhisperSTTService:
    """Returns the shared WhisperSTTService instance."""
    global _whisper_service
    if _whisper_service is None:
        _whisper_service = WhisperSTTService()
    return _whisper_service
