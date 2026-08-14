"""
NOT USED in v1.
 
The current call flow (webhooks/speech.py) relies on Twilio's built-in
speech recognition via <Gather input="speech">, which returns transcribed
text directly in the webhook payload — no separate STT step needed.
 
This file would only become relevant if we switch to <Record>-ing raw
audio and sending it to an external STT provider (e.g. Whisper) instead,
for better accuracy/control than Twilio's built-in recognizer.
 
Confirm with the team before implementing — avoid building a second,
possibly conflicting STT path alongside the working Gather-based one.
"""
 