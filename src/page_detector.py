import re
from collections import Counter

# Primary obituary keywords with weights (higher = stronger signal)
OBITUARY_KEYWORDS = {
    # Strongest signals
    "obituary": 10, "obituaries": 10,
    "death notice": 9, "death notices": 9,
    "in memoriam": 9, "memoriam": 8,
    "passed away": 8, "passed on": 7,
    "rest in peace": 8, "rip": 5,
    # Strong signals
    "condolence": 7, "condolences": 7,
    "funeral notice": 7, "funeral": 5,
    "memorial service": 7, "memorial": 6,
    "remembrance": 6, "remembering": 5,
    "departed": 6, "late": 4,
    "beloved": 5, "dearly beloved": 7,
    "tribute": 5,
    # Moderate signals
    "death": 4, "deaths": 4,
    "died": 4, "passed": 3,
    "survived by": 6, "is survived by": 7,
    "widow": 5, "widower": 5,
    "bereaved": 5, "mourning": 4,
    "laid to rest": 6, "cremation": 5, "interment": 5,
    "condole": 5, "mourn": 4,
}

# Patterns that detect age mentions in obituary text
AGE_PATTERNS = [
    r'\baged?\s*\d{1,3}\b',
    r'\b\d{1,3}\s*years?\s*old\b',
    r'\b\d{1,3}\s*yrs?\b',
    r'\(\d{2,3}\)',
    r'\b\d{4}\s*[–\-]\s*\d{4}\b',  # birth-death year range
]

# Classification labels and thresholds
LABEL_OBITUARY = "OBITUARY"
LABEL_DEATH_NOTICES = "DEATH NOTICES"
LABEL_MEMORIAL = "MEMORIAL / POSSIBLE OBITUARY"
LABEL_NOT_RELEVANT = "NOT RELEVANT"


def _count_keyword_score(text_lower, word_count):
    """
    Counts weighted keyword hits and normalizes by word density.
    Returns a raw score.
    """
    raw_score = 0
    keyword_hits = 0
    
    for keyword, weight in OBITUARY_KEYWORDS.items():
        count = text_lower.count(keyword)
        if count > 0:
            # Cap contribution per keyword to avoid one word dominating
            capped_count = min(count, 5)
            raw_score += capped_count * weight
            keyword_hits += count
    
    return raw_score, keyword_hits


def _count_age_patterns(text):
    """Returns the number of age-like patterns found in text."""
    count = 0
    for pattern in AGE_PATTERNS:
        count += len(re.findall(pattern, text, re.IGNORECASE))
    return count


def _count_name_patterns(text):
    """
    Counts lines that look like person names:
    - All-caps short lines (e.g. JOHN MATHEW)
    - Title-case short lines (2-4 words) near the top of an entry
    """
    count = 0
    for line in text.split('\n'):
        line = line.strip()
        words = line.split()
        if 1 < len(words) <= 5:
            if line.isupper() or all(w[0].isupper() for w in words if w[0].isalpha()):
                count += 1
    return count


def score_page(text):
    """
    Calculates an Obituary Relevance Score (0–100) for a given page's text.
    
    Returns:
        dict with keys: score (int), label (str), keyword_hits (int),
                        age_patterns (int), name_patterns (int)
    """
    if not text or len(text.strip()) < 20:
        return {"score": 0, "label": LABEL_NOT_RELEVANT,
                "keyword_hits": 0, "age_patterns": 0, "name_patterns": 0}

    text_lower = text.lower()
    words = text_lower.split()
    word_count = max(len(words), 1)

    # 1. Keyword score (0–60 points)
    raw_kw_score, keyword_hits = _count_keyword_score(text_lower, word_count)
    # Normalize: density per 100 words
    density = (keyword_hits / word_count) * 100
    # Scale to 0–60
    kw_score = min(60, raw_kw_score * 0.8 + density * 2)

    # 2. Age pattern score (0–20 points)
    age_count = _count_age_patterns(text)
    age_score = min(20, age_count * 4)

    # 3. Name pattern score (0–20 points)
    name_count = _count_name_patterns(text)
    name_score = min(20, name_count * 2)

    total_score = int(kw_score + age_score + name_score)
    total_score = min(100, total_score)

    # Classify
    if total_score >= 80:
        label = LABEL_OBITUARY
    elif total_score >= 60:
        label = LABEL_DEATH_NOTICES
    elif total_score >= 35:
        label = LABEL_MEMORIAL
    else:
        label = LABEL_NOT_RELEVANT

    return {
        "score": total_score,
        "label": label,
        "keyword_hits": keyword_hits,
        "age_patterns": age_count,
        "name_patterns": name_count,
    }


def is_relevant_page(score_result, threshold=35):
    """Returns True if the page is worth extracting entries from."""
    return score_result["score"] >= threshold
