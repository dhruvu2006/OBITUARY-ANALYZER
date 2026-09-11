import re

# Age extraction patterns (ordered by specificity)
AGE_PATTERNS = [
    (r'\baged?\s*(\d{1,3})\s*years?\b', 'direct'),
    (r'\baged?\s*(\d{1,3})\b', 'direct'),
    (r'\b(\d{1,3})\s*years?\s*old\b', 'direct'),
    (r'\b(\d{1,3})\s*yrs?\b', 'direct'),
    (r'\((\d{2,3})\)', 'direct'),
    (r'\b(\d{1,3})\s*-\s*year\s*-\s*old\b', 'direct'),
]

YEAR_RANGE_PATTERN = re.compile(r'\b(1[89]\d{2}|20[012]\d)\s*[–\-]\s*(20[012]\d|1[89]\d{2})\b')

NOTICE_KEYWORDS = {
    'obituary': 'Obituary',
    'obituaries': 'Obituary',
    'death notice': 'Death Notice',
    'death notices': 'Death Notice',
    'memorial': 'Memorial',
    'in memoriam': 'Memorial',
    'remembrance': 'Remembrance',
    'condolence': 'Condolence',
    'condolences': 'Condolence',
    'funeral notice': 'Funeral Notice',
    'funeral': 'Funeral Notice',
    'passed away': 'Death Notice',
    'tribute': 'Tribute',
}

TITLE_PREFIXES = re.compile(r'^(Mr\.?|Mrs\.?|Ms\.?|Dr\.?|Prof\.?|Sri\.?|Smt\.?|Late\s)', re.IGNORECASE)


def _extract_age(text):
    """
    Attempts to extract an age value from text.
    Returns (age: int or None, source: str)
    """
    for pattern, source in AGE_PATTERNS:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            try:
                age = int(match.group(1))
                if 1 <= age <= 120:
                    return age, source
            except ValueError:
                pass

    # Try year-range pattern (e.g. 1942–2026)
    match = YEAR_RANGE_PATTERN.search(text)
    if match:
        try:
            birth = int(match.group(1))
            death = int(match.group(2))
            age = death - birth
            if 1 <= age <= 120:
                return age, 'calculated'
        except ValueError:
            pass

    return None, 'unknown'


def _clean_name(name):
    """Cleans a potential name string."""
    name = TITLE_PREFIXES.sub('', name).strip()
    name = re.sub(r'[^\w\s\-\']', '', name).strip()
    # Require at least 2 chars and a space (likely first + last)
    if len(name) < 3:
        return None
    return name.title()


def _detect_notice_type(block_text):
    """Detects the notice type from the surrounding text block."""
    text_lower = block_text.lower()
    for keyword, notice_type in NOTICE_KEYWORDS.items():
        if keyword in text_lower:
            return notice_type
    return 'Unknown'


def _calculate_confidence(name, age, age_source, block_text):
    """
    Returns a confidence score (0.0–1.0) for an extracted entry.
    Based on how clearly name and age were found.
    """
    score = 0.5  # base

    # Name quality
    if name and len(name.split()) >= 2:
        score += 0.2
    elif name:
        score += 0.1

    # Age quality
    if age_source == 'direct':
        score += 0.25
    elif age_source == 'calculated':
        score += 0.1

    # Block contains obituary keywords
    obit_words = ['passed away', 'died', 'death', 'late', 'beloved', 'obituary']
    if any(w in block_text.lower() for w in obit_words):
        score += 0.05

    return round(min(score, 1.0), 2)


def extract_obituaries(cleaned_text, page_num=0):
    """
    Extracts obituary entries from cleaned OCR text.
    
    Returns a list of dicts with keys:
        Name, Age, Age_Source, Page, Notice_Type, Location, Date, Confidence
    """
    entries = []
    seen = set()

    # Split into blocks (separated by blank lines)
    blocks = re.split(r'\n{2,}', cleaned_text)

    for block in blocks:
        block = block.strip()
        if not block or len(block) < 10:
            continue

        lines = [l.strip() for l in block.split('\n') if l.strip()]
        if not lines:
            continue

        age, age_source = _extract_age(block)
        if age is None:
            # Try scanning individual lines for age
            for line in lines:
                age, age_source = _extract_age(line)
                if age:
                    break

        # Name: look at first 1-2 lines of block for a name-like string
        name = None
        for candidate_line in lines[:3]:
            words = candidate_line.split()
            if 1 < len(words) <= 5:
                is_caps = candidate_line.isupper()
                is_title = all(w[0].isupper() for w in words if w[0].isalpha())
                if is_caps or is_title:
                    cleaned = _clean_name(candidate_line)
                    if cleaned:
                        name = cleaned
                        break

        # If we found an age but not a name, skip
        if not name:
            continue

        # Deduplicate
        dedup_key = (name.lower(), str(age))
        if dedup_key in seen:
            continue
        seen.add(dedup_key)

        notice_type = _detect_notice_type(block)
        confidence = _calculate_confidence(name, age, age_source, block)

        # Try to extract a date (basic)
        date_match = re.search(
            r'\b(\d{1,2}[\s\-/]\w+[\s\-/]\d{2,4}|\w+\s+\d{1,2},?\s+\d{4})\b',
            block
        )
        date_str = date_match.group(0) if date_match else 'Unknown'

        entries.append({
            "Name": name,
            "Age": str(age) if age else 'Unknown',
            "Age_Source": age_source,
            "Page": page_num,
            "Notice_Type": notice_type,
            "Location": 'Unknown',
            "Date": date_str,
            "Confidence": confidence,
        })

    # Fallback: if no entries found via blocks, try a linear scan
    if not entries:
        entries = _fallback_linear_scan(cleaned_text, page_num)

    return entries


def _fallback_linear_scan(text, page_num):
    """
    Fallback extractor: scan lines sequentially.
    Tries to pair capitalized name-like lines with a nearby age pattern.
    """
    entries = []
    lines = text.split('\n')
    seen = set()

    for i, line in enumerate(lines):
        line = line.strip()
        if not line:
            continue

        age, age_source = _extract_age(line)
        if not age:
            continue

        # Search 5 lines upward for a name
        name = None
        for j in range(max(0, i - 5), i + 1):
            candidate = lines[j].strip()
            words = candidate.split()
            if 1 < len(words) <= 5:
                if candidate.isupper() or all(w[0].isupper() for w in words if w[0].isalpha()):
                    cleaned = _clean_name(candidate)
                    if cleaned:
                        name = cleaned
                        break

        if not name:
            continue

        key = (name.lower(), str(age))
        if key in seen:
            continue
        seen.add(key)

        context = '\n'.join(lines[max(0, i-3):min(len(lines), i+3)])
        entries.append({
            "Name": name,
            "Age": str(age),
            "Age_Source": age_source,
            "Page": page_num,
            "Notice_Type": _detect_notice_type(context),
            "Location": 'Unknown',
            "Date": 'Unknown',
            "Confidence": _calculate_confidence(name, age, age_source, context),
        })

    return entries
