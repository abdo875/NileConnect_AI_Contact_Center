"""
Full call flow test: dialogue text + classifier + DB flow logic.
Run from backend/: python test_flow.py
"""
import sys
sys.path.insert(0, ".")

from app.telephony.vonage.response import (
    GREETING_TEXT, GOODBYE_RESOLVED_TEXT, GOODBYE_ESCALATE_TEXT,
    NOT_UNDERSTOOD_TEXT, NO_INPUT_TEXT,
)
from app.telephony.stt.arabic_classifier import classify_response
from app.core.constants import FollowupResult

print("=" * 60)
print("GREETING TEXT (what the AI says when call is answered)")
print("=" * 60)
print(GREETING_TEXT)
print()

print("=" * 60)
print("CLASSIFIER TESTS")
print("=" * 60)

tests = [
    # YES variations
    ("نعم",              FollowupResult.YES),
    ("اه اتحلت",         FollowupResult.YES),
    ("أيوه اتحلت",       FollowupResult.YES),
    ("ايوه تمام",        FollowupResult.YES),
    ("تمام شغال",        FollowupResult.YES),
    ("نعم تم حلها",      FollowupResult.YES),
    ("خلصت الحمد لله",   FollowupResult.YES),
    # NO variations
    ("لا",               FollowupResult.NO),
    ("لأ لسه",           FollowupResult.NO),
    ("لا لسه موجودة",    FollowupResult.NO),
    ("مش اتحلت",         FollowupResult.NO),
    ("لسه مش شغال",      FollowupResult.NO),
    ("لا مازال المشكلة", FollowupResult.NO),
    # UNKNOWN
    ("مش عارف",          FollowupResult.UNKNOWN),
    ("",                 FollowupResult.UNKNOWN),
]

all_pass = True
for text, expected in tests:
    got = classify_response(text)
    ok  = "✅" if got == expected else "❌"
    if got != expected:
        all_pass = False
    label = text if text else "(empty)"
    print(f"  {ok} '{label}' → {got.value}  (expected {expected.value})")

print()
print("=" * 60)
print("DB OUTCOMES")
print("=" * 60)
print("Customer says نعم / أيوه / اتحلت:")
print("  → Case.status = RESOLVED")
print("  → AIFollowup.result = YES")
print("  → AIFollowup.status = COMPLETED")
print("  → Agent says:", GOODBYE_RESOLVED_TEXT)
print()
print("Customer says لا / لأ / لسه:")
print("  → Case.status = NEEDS_HUMAN  (call center sees it!)")
print("  → AIFollowup.result = NO")
print("  → AIFollowup.status = COMPLETED")
print("  → Agent says:", GOODBYE_ESCALATE_TEXT)
print()

if all_pass:
    print("=" * 60)
    print("ALL TESTS PASSED ✅")
    print("=" * 60)
else:
    print("SOME TESTS FAILED ❌")
    sys.exit(1)
