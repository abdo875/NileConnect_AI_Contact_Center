# -*- coding: utf-8 -*-
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.path.insert(0, ".")

from app.telephony.stt.arabic_classifier import classify_response
from app.core.constants import FollowupResult

tests = [
    ("نعم",                          FollowupResult.YES),
    ("اه اتحلت",                     FollowupResult.YES),
    ("أيوه اتحلت",                   FollowupResult.YES),
    ("تمام شغال",                    FollowupResult.YES),
    ("نعم تم حلها",                  FollowupResult.YES),
    ("لا",                           FollowupResult.NO),
    ("لأ لسه",                       FollowupResult.NO),
    ("لا لسه موجودة",                FollowupResult.NO),
    ("مش اتحلت",                     FollowupResult.NO),
    ("لسه مش شغال",                  FollowupResult.NO),
    ("مش عارف",                      FollowupResult.UNKNOWN),
    ("",                             FollowupResult.UNKNOWN),
]

passed = 0
for text, exp in tests:
    got = classify_response(text)
    ok = got == exp
    if ok:
        passed += 1
    status = "PASS" if ok else "FAIL"
    label = repr(text) if text else "(empty)"
    print(f"[{status}] {label:30s}  expected={exp.value:7s}  got={got.value}")

print()
print(f"Results: {passed}/{len(tests)} passed")
sys.exit(0 if passed == len(tests) else 1)
