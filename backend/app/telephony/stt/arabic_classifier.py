"""
Classifies a transcribed Arabic customer response into YES / NO / UNKNOWN.
 
Deliberately keyword-based rather than ML-based for v1: speech from Twilio's
Arabic STT is short (one phrase answering a yes/no question), and this is
fully testable offline with zero external dependencies or cost. If this
proves too brittle in real calls, the natural upgrade later is a single
LLM call with a strict "answer only YES, NO, or UNKNOWN" prompt.
"""
import re
from app.core.constants import FollowupResult
 
# Common ways an Egyptian Arabic speaker confirms the problem is solved.
# Kept intentionally broad (dialect + formal Arabic) since real customers
# won't use uniform phrasing.
YES_KEYWORDS = [
    "أيوه", "ايوه", "أيوا", "ايوا", "نعم", "تمام", "اتحلت", "اتحل",
    "حلت", "حلّت", "خلصت", "كويس", "كويسة", "شغال", "شغالة", "تم",
    "اه", "آه", "ماشي", "ok", "okay",
]
 
# Common ways a customer says the problem is NOT solved.
NO_KEYWORDS = [
    "لأ", "لا", "مش", "لسه", "لسة", "برضو", "برضه", "موجودة", "موجود",
    "مفيش فايدة", "زي ما هي", "مش شغال", "مش شغالة", "عطلانة", "واقفة",
]
 
 
def _normalize(text: str) -> str:
    """Lowercase, strip Arabic diacritics/punctuation noise for matching."""
    text = text.strip().lower()
    # Strip common punctuation Twilio's STT sometimes includes.
    text = re.sub(r"[.,!؟?]", "", text)
    return text
 
 
def classify_response(speech_text: str) -> FollowupResult:
    """
    Classifies a raw transcript into YES, NO, or UNKNOWN.
 
    NOTE: checks NO_KEYWORDS first on purpose. Arabic "لأ" (no) can appear
    as a standalone negator inside longer NO sentences that might also
    contain incidental YES-like tokens (e.g. "لأ, لسه لأ" repeating "no").
    Checking NO first avoids YES keywords accidentally winning in mixed
    phrases.
    """
    if not speech_text or not speech_text.strip():
        return FollowupResult.UNKNOWN
 
    normalized = _normalize(speech_text)
 
    has_no = any(keyword in normalized for keyword in NO_KEYWORDS)
    has_yes = any(keyword in normalized for keyword in YES_KEYWORDS)
 
    if has_no and not has_yes:
        return FollowupResult.NO
    if has_yes and not has_no:
        return FollowupResult.YES
 
    # Both matched (ambiguous/contradictory phrase) or neither matched
    # (unrecognized phrasing) — let the call flow ask the customer to repeat.
    return FollowupResult.UNKNOWN
 