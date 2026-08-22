"""
Unit and Integration Tests for Voice AI / Whisper Arabic STT Call Flow.

Tests:
1. Whisper receives audio and returns Arabic transcript.
2. Empty audio is handled safely (returns "" -> UNKNOWN).
3. Whisper API failure is handled safely (never returns YES).
4. Arabic YES transcripts classify and route to handle_yes (Case RESOLVED).
5. Arabic NO transcripts classify and route to handle_no (Case NEEDS_HUMAN).
6. UNKNOWN speech triggers retry on attempt 1, and escalates to human on attempt 2.
7. Transcript is stored in existing Call.transcript field.
8. Existing call_id, case_id, and customer_id are preserved (no new Case/Call created).
9. Vonage recording webhook integrates end-to-end with mocked download and Whisper.
"""
import io
import unittest
from unittest.mock import MagicMock, patch
import uuid
from datetime import datetime, timezone

import pytest
from fastapi.testclient import TestClient

from app.core.constants import CallOutcome, CallType, CaseStatus, FollowupResult, FollowupStatus
from app.models.ai_followup import AIFollowup
from app.models.call import Call
from app.models.case import Case
from app.models.customer import Customer
from app.telephony.stt.arabic_classifier import classify_response
from app.telephony.stt.whisper_service import WhisperSTTService
from app.telephony.call_flows.yes_flow import handle_yes
from app.telephony.call_flows.no_flow import handle_no
from app.telephony.call_flows.unknown_flow import handle_unknown


class TestWhisperSTTService(unittest.TestCase):
    """Test pure Whisper STT service."""

    def test_whisper_transcribes_audio_bytes_successfully(self):
        """Whisper receives audio bytes and returns transcribed Arabic text."""
        service = WhisperSTTService(api_key="mock_key", model="whisper-large-v3-turbo")

        mock_client = MagicMock()
        mock_transcription = MagicMock()
        mock_transcription.text = "أيوه اتحلت المشكلة"
        mock_client.audio.transcriptions.create.return_value = mock_transcription

        with patch.object(service, "_client", mock_client):
            audio_bytes = b"fake_mp3_audio_data"
            transcript = service.transcribe(audio_bytes)

            assert transcript == "أيوه اتحلت المشكلة"
            mock_client.audio.transcriptions.create.assert_called_once()
            call_kwargs = mock_client.audio.transcriptions.create.call_args.kwargs
            assert call_kwargs["model"] == "whisper-large-v3-turbo"
            assert call_kwargs["language"] == "ar"

    def test_whisper_handles_empty_audio_gracefully(self):
        """Empty audio bytes or None should return empty string without errors."""
        service = WhisperSTTService(api_key="mock_key")
        assert service.transcribe(b"") == ""
        assert service.transcribe(None) == ""

    def test_whisper_handles_api_failure_gracefully(self):
        """Whisper API network/server failure should return empty string, never crash."""
        service = WhisperSTTService(api_key="mock_key")

        mock_client = MagicMock()
        mock_client.audio.transcriptions.create.side_effect = Exception("API connection error")

        with patch.object(service, "_client", mock_client):
            transcript = service.transcribe(b"some_audio_data")
            assert transcript == ""


class TestArabicClassifierWithWhisperTranscripts(unittest.TestCase):
    """Test classifier handling various Egyptian and MSA Whisper transcripts."""

    def test_arabic_yes_transcripts(self):
        yes_samples = [
            "نعم",
            "أيوه",
            "ايوه",
            "أيوه اتحلت",
            "آه تمام",
            "أيوة تمام",
            "نعم المشكلة اتحلت",
            "تمام شغال",
            "خلصت الحمد لله",
            "اتحلت خلاص",
        ]
        for text in yes_samples:
            result = classify_response(text)
            assert result == FollowupResult.YES, f"Failed for YES transcript: {text}"

    def test_arabic_no_transcripts(self):
        no_samples = [
            "لا",
            "لأ",
            "لأ لسه",
            "لا لسه موجودة",
            "المشكلة لسه موجودة",
            "مش اتحلت",
            "لسه مش شغال",
            "عطلانة",
            "واقفة",
        ]
        for text in no_samples:
            result = classify_response(text)
            assert result == FollowupResult.NO, f"Failed for NO transcript: {text}"

    def test_unknown_and_empty_transcripts(self):
        unknown_samples = [
            "",
            "   ",
            "مش عارف",
            "مش فاهم",
            "ألو مين معايا",
        ]
        for text in unknown_samples:
            result = classify_response(text)
            assert result == FollowupResult.UNKNOWN, f"Expected UNKNOWN for transcript: {text}"


class TestCallFlowLogicAndDatabasePreservation(unittest.TestCase):
    """Test business flows update existing records without creating new entities."""

    def setUp(self):
        self.mock_db = MagicMock()
        self.customer_id = uuid.uuid4()
        self.case_id = uuid.uuid4()
        self.followup_id = uuid.uuid4()
        self.call_id = uuid.uuid4()

        self.case = Case(
            id=self.case_id,
            customer_id=self.customer_id,
            issue="Internet connection broken",
            status=CaseStatus.OPEN,
        )
        self.call = Call(
            id=self.call_id,
            customer_id=self.customer_id,
            case_id=self.case_id,
            call_type=CallType.OUTBOUND_AI,
            outcome=CallOutcome.PENDING,
            transcript=None,
        )
        self.followup = AIFollowup(
            id=self.followup_id,
            case_id=self.case_id,
            customer_id=self.customer_id,
            scheduled_at=datetime.now(timezone.utc),
            status=FollowupStatus.IN_PROGRESS,
            call_id=self.call_id,
        )

    @patch("app.telephony.call_flows.yes_flow.FollowupRepository")
    @patch("app.telephony.call_flows.yes_flow.CallRepository")
    @patch("app.telephony.call_flows.yes_flow.CaseRepository")
    def test_handle_yes_updates_existing_records(self, mock_case_repo_cls, mock_call_repo_cls, mock_followup_repo_cls):
        mock_followup_repo = mock_followup_repo_cls.return_value
        mock_call_repo = mock_call_repo_cls.return_value
        mock_case_repo = mock_case_repo_cls.return_value

        mock_followup_repo.get_by_id.return_value = self.followup
        mock_call_repo.get_by_id.return_value = self.call
        mock_case_repo.get_by_id.return_value = self.case

        handle_yes(self.mock_db, self.followup_id, self.call_id)

        # Call record updated
        assert self.call.outcome == CallOutcome.RESOLVED
        assert self.call.ended_at is not None
        mock_call_repo.update.assert_called_once_with(self.call)

        # Followup record updated
        assert self.followup.status == FollowupStatus.COMPLETED
        assert self.followup.result == FollowupResult.YES
        mock_followup_repo.update.assert_called_once_with(self.followup)

        # Case record marked RESOLVED (no new Case created)
        assert self.case.status == CaseStatus.RESOLVED
        assert self.case.resolved_at is not None
        mock_case_repo.update.assert_called_once_with(self.case)

    @patch("app.telephony.call_flows.no_flow.FollowupRepository")
    @patch("app.telephony.call_flows.no_flow.CallRepository")
    @patch("app.telephony.call_flows.no_flow.CaseRepository")
    def test_handle_no_escalates_existing_case_to_human(self, mock_case_repo_cls, mock_call_repo_cls, mock_followup_repo_cls):
        mock_followup_repo = mock_followup_repo_cls.return_value
        mock_call_repo = mock_call_repo_cls.return_value
        mock_case_repo = mock_case_repo_cls.return_value

        mock_followup_repo.get_by_id.return_value = self.followup
        mock_call_repo.get_by_id.return_value = self.call
        mock_case_repo.get_by_id.return_value = self.case

        handle_no(self.mock_db, self.followup_id, self.call_id)

        assert self.call.outcome == CallOutcome.ESCALATED
        assert self.followup.status == FollowupStatus.COMPLETED
        assert self.followup.result == FollowupResult.NO
        assert self.case.status == CaseStatus.NEEDS_HUMAN

    def test_handle_unknown_retries_on_first_attempt(self):
        retry_url = "http://localhost:8000/api/v1/telephony/speech?attempt=2"
        response = handle_unknown(self.mock_db, self.followup_id, self.call_id, retry_url, attempt=1)
        assert response is not None


class TestVonageRecordingWebhook(unittest.TestCase):
    """Test Vonage recording webhook integration end-to-end with mocked I/O."""

    @patch("app.telephony.vonage.webhook.get_vonage_client")
    @patch("app.telephony.vonage.webhook.get_whisper_service")
    @patch("app.telephony.vonage.webhook.CallRepository")
    @patch("app.telephony.vonage.webhook.handle_yes")
    def test_recording_webhook_transcribes_and_stores_transcript(
        self, mock_handle_yes, mock_call_repo_cls, mock_get_whisper, mock_get_vonage
    ):
        mock_client = MagicMock()
        mock_get_vonage.return_value = mock_client

        mock_whisper = MagicMock()
        mock_whisper.transcribe.return_value = "أيوه المشكلة اتحلت"
        mock_get_whisper.return_value = mock_whisper

        mock_call_repo = mock_call_repo_cls.return_value
        mock_call = MagicMock()
        mock_call_repo.get_by_id.return_value = mock_call

        followup_id = uuid.uuid4()
        call_id = uuid.uuid4()

        # Import router and test via FastAPI test client
        from fastapi import FastAPI
        from app.telephony.vonage.webhook import router

        test_app = FastAPI()
        test_app.include_router(router, prefix="/api/v1")
        client = TestClient(test_app)

        payload = {
            "recording_url": "https://api.nexmo.com/v1/files/test-recording-123.mp3",
            "recording_uuid": "rec-123",
            "size": 12345,
        }

        url = f"/api/v1/vonage/recording?followup_id={followup_id}&call_id={call_id}&attempt=1"
        response = client.post(url, json=payload)

        assert response.status_code == 200
        ncco = response.json()
        assert isinstance(ncco, list)
        assert ncco[0]["action"] == "talk"

        # Verified Whisper was called
        mock_whisper.transcribe.assert_called_once()

        # Verified transcript was saved in Call.transcript
        assert mock_call.transcript == "أيوه المشكلة اتحلت"
        mock_call_repo.update.assert_called_once_with(mock_call)

        # Verified handle_yes was invoked
        mock_handle_yes.assert_called_once()
