"""
Direct Vonage call test — bypasses the whole FastAPI stack.
Run from backend/ directory: python test_call.py
"""
import sys
sys.path.insert(0, ".")

from app.core.config import settings
from pathlib import Path

print("=" * 50)
print("CONFIG CHECK")
print("=" * 50)
print(f"Application ID : [{settings.VONAGE_APPLICATION_ID}]")
print(f"FROM           : [{settings.VONAGE_FROM_NUMBER}]")
print(f"TO             : [{settings.VONAGE_TO_NUMBER}]")

key = Path(settings.VONAGE_PRIVATE_KEY_PATH)
resolved = (Path(".") / key).resolve()
print(f"Key path       : {resolved}")
print(f"Key exists     : {resolved.exists()}")
print()

print("=" * 50)
print("BUILDING CLIENT")
print("=" * 50)
from app.telephony.vonage.client import get_vonage_client, get_from_number, get_to_number
try:
    client = get_vonage_client()
    print(f"[OK] Client ready: {type(client).__name__}")
except Exception as e:
    print(f"[FAIL] {type(e).__name__}: {e}")
    sys.exit(1)

print()
print("=" * 50)
print("PLACING CALL")
print("=" * 50)
print(f"FROM: {get_from_number()}")
print(f"TO  : {get_to_number()}")

from vonage_voice import CreateCallRequest, Phone, ToPhone

ncco = [
    {
        "action": "talk",
        "text": "\u0645\u0631\u062d\u0628\u0627\u060c \u0647\u0630\u0627 \u0627\u062e\u062a\u0628\u0627\u0631 \u0645\u0646 \u0646\u0627\u064a\u0644 \u0643\u0648\u0646\u0643\u062a.",
        "language": "ar",
    }
]

try:
    resp = client.voice.create_call(
        CreateCallRequest(
            to=[ToPhone(number=get_to_number())],
            from_=Phone(number=get_from_number()),
            ncco=ncco,
        )
    )
    print()
    print("[OK] CALL PLACED SUCCESSFULLY!")
    print(f"UUID: {getattr(resp, 'uuid', str(resp))}")
    print(f"Status: {getattr(resp, 'status', 'unknown')}")
    print("The phone should ring in a few seconds...")

except Exception as e:
    print()
    print(f"[FAIL] {type(e).__name__}")
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
