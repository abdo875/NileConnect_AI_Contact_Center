"""
NOT USED in v1.
 
The current call flow (twilio/response.py) uses Twilio's built-in
<Say voice="Polly.Zeina"> for Arabic text-to-speech directly in TwiML —
no separate TTS step needed.
 
This file would only become relevant if we switch to an external TTS
provider (e.g. ElevenLabs) for higher-quality Arabic voice than Twilio's
built-in Polly voice, generating audio files and playing them via <Play>
instead of <Say>.
 
Confirm with the team before implementing — avoid building a second,
possibly conflicting TTS path alongside the working Say-based one.
"""
 