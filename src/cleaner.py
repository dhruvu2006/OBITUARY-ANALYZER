import re

def clean_ocr_text(raw_text):
    """
    Cleans raw OCR text for use in downstream extraction.
    - Normalizes line breaks.
    - Removes obvious OCR garbage characters.
    - Preserves punctuation useful for name/age detection.
    """
    if not raw_text:
        return ""

    # Normalize line endings
    cleaned = raw_text.replace('\r\n', '\n').replace('\r', '\n')

    # Remove lines that are pure noise (single characters, lone numbers > 4 digits, etc.)
    lines = []
    for line in cleaned.split('\n'):
        stripped = line.strip()
        # Keep lines that have at least 2 alphanumeric chars
        if len(re.sub(r'[^a-zA-Z0-9]', '', stripped)) >= 2:
            lines.append(stripped)
        elif stripped == '':
            lines.append('')  # Preserve blank lines as separators

    cleaned = '\n'.join(lines)

    # Collapse 3+ blank lines to 2 (preserve entry separations)
    cleaned = re.sub(r'\n{3,}', '\n\n', cleaned)

    # Remove stray special chars that OCR commonly adds
    cleaned = re.sub(r'[|}{\\<>~^`]', '', cleaned)

    return cleaned.strip()
