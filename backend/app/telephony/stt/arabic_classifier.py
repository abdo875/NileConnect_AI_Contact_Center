"""
Classifies a transcribed Arabic customer response into YES / NO / UNKNOWN.

Keyword-based classifier for short Arabic yes/no answers.
Covers both Egyptian dialect AND Modern Standard Arabic (MSA).
"""
import re
from app.core.constants import FollowupResult

# ── YES keywords ───────────────────────────────────────────────────────────────
YES_KEYWORDS = [
    # Egyptian dialect
    "ايوه", "ايوا", "أيوه", "أيوة", "ايوة", "اه", "آه",
    # MSA
    "نعم", "صح", "صحيح",
    # Resolution words
    "اتحلت", "اتحل", "حلت", "انحلت", "خلصت", "خلص",
    # Working / good
    "شغاله", "شغال", "كويسه", "كويس", "تمام", "ماشي",
    # Done
    "خلاص", "ok", "okay",
]

# ── NO keywords ────────────────────────────────────────────────────────────────
NO_KEYWORDS = [
    # Hard no
    "لا", "لأ",
    # Still there
    "لسه", "لسة", "مازال", "ما زال",
    # Not + something (we check "مش" separately below)
    "موجوده", "موجود", "مستمره", "مستمر",
    # Useless / same
    "برضو", "برضه",
    # Broken
    "عطلانه", "عطلان", "واقفه", "واقف",
]

# Negation word — means NO only when negating a YES word (e.g. مش اتحلت)
# If it negates an unknown word (e.g. مش عارف), treat as UNKNOWN
MSH_WORD = "مش"


def _normalize(text: str) -> str:
    """
    Normalise Arabic text for keyword matching.
    - Lowercase
    - Remove diacritics (tashkeel) and punctuation
    - Unify taa marbuta (ة → ه) — very common variant in typed/STT text
    """
    text = text.strip().lower()
    # Remove punctuation
    text = re.sub(r"[.,!؟?،؛]", " ", text)
    # Remove Arabic tashkeel (diacritics U+064B – U+065F)
    text = re.sub(r"[\u064b-\u065f]", "", text)
    # Unify taa marbuta variants
    text = text.replace("ة", "ه")
    # Collapse multiple spaces
    text = re.sub(r"\s+", " ", text).strip()
    return text


def _matches_keywords(text: str, words: set[str], keywords: list[str]) -> bool:
    """Checks if any phrase or standalone word keyword is matched in text."""
    for kw in keywords:
        if " " in kw:
            if kw in text:
                return True
        else:
            if kw in words:
                return True
    return False


def classify_response(speech_text: str) -> FollowupResult:
    """
    Classify a raw Arabic transcript into YES, NO, or UNKNOWN.

    Logic:
    1. Normalize text.
    2. Check NO keywords first (prevents false YES in mixed phrases).
    3. Check YES keywords.
    4. Special handling for "مش" (negator word).
    5. Return UNKNOWN if ambiguous or unrecognised.
    """
    if not speech_text or not speech_text.strip():
        return FollowupResult.UNKNOWN

    normalized = _normalize(speech_text)
    words = set(normalized.split())

    has_no = _matches_keywords(normalized, words, NO_KEYWORDS)
    has_yes = _matches_keywords(normalized, words, YES_KEYWORDS)
    has_msh = MSH_WORD in words

    # مش + YES_word → NO  (e.g. "مش اتحلت", "مش شغال", "مش تمام")
    msh_negates_yes = has_msh and has_yes
    # مش + unknown word → UNKNOWN  (e.g. "مش عارف", "مش فاهم")
    msh_alone = has_msh and not has_yes and not has_no

    is_no = has_no or msh_negates_yes
    is_yes = has_yes and not has_no and not has_msh

    if is_no and not (msh_alone):
        return FollowupResult.NO
    if is_yes:
        return FollowupResult.YES

    # Ambiguous or unrecognised → ask the customer to repeat
    return FollowupResult.UNKNOWN