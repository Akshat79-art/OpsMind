import re
import unicodedata

from noise_detection import LOW_CONF_THRESHOLD
from noise_detection import noise_key, page_number, NoiseProfile

IMAGE_ONLY = re.compile(r"^\s*!\[[^\]]*\]\([^)]*\)\s*$")
IMAGE_INLINE = re.compile(r"!\[[^\]]*\]\([^)]*\)")

def is_line_noise(line: str, record: dict, profile: NoiseProfile, conf: float) -> bool:
    '''
    Checks if the line is noise.
    '''
    if not line.strip():
        return False                                   # blank -> not noise (collapsed later)

    # 1. repeated boilerplate (header/footer)
    key = noise_key(line)
    if key in profile.header_keys or key in profile.footer_keys:
        return True

    # 2. page-number line, by offset equality (only when offset trusted)
    page = record.get("page")
    if profile.offset is not None and isinstance(page, int) and conf >= LOW_CONF_THRESHOLD:
        n = page_number([line])
        if n is not None and n == page - profile.offset:
            return True

    return False


def strip_images(lines: list[str]) -> list[str]:
    '''
    Looks through a record's lines and removes the ones that are just image markup.
    It also strips inline image snippets that sit inside an otherwise normal line.
    '''
    kept = []
    for line in lines:
        if IMAGE_ONLY.match(line):
            continue
        kept.append(IMAGE_INLINE.sub("", line))
    return kept


def rejoin_hyphenation(lines: list[str]) -> str:
    '''
    Merges words split across line breaks by a trailing hyphen.
    Handling both "comput-" + "er" and "comput -" + "er" -> "computer".
    Returns the lines joined into a single string.
    '''
    merged: list[str] = []
    for line in lines:
        if merged and re.search(r"\S\s*-\s*$", merged[-1]):
            merged[-1] = re.sub(r"\s*-\s*$", "", merged[-1]) + line.lstrip()
        else:
            merged.append(line)
    return "\n".join(merged)


def clean_text(text: str, record: dict, profile: NoiseProfile, conf: float) -> str:
    '''
    Cleans a single record's text: drops noise lines and images, rejoins
    hyphenated words, normalizes unicode, and collapses whitespace.
    Returns the cleaned text.
    '''
    lines = [line for line in text.splitlines() if not is_line_noise(line, record, profile, conf)]
    lines = strip_images(lines)
    joined = rejoin_hyphenation(lines)
    normalized = unicodedata.normalize("NFKC", joined)
    normalized = re.sub(r"\n{3,}", "\n\n", normalized)
    normalized = re.sub(r"[ \t]+\n", "\n", normalized)
    return normalized.strip()


def normalize_records(records: list[dict], profile: NoiseProfile) -> list[dict]:
    '''
    Cleans every record's text using the noise profile, returning new
    record dicts with the "text" field replaced. The input is untouched.
    '''
    cleaned: list[dict] = []
    for i, record in enumerate(records):
        conf = profile.record_conf[i] if i < len(profile.record_conf) else 1.0
        new_record = dict(record)
        new_record["text"] = clean_text(record["text"], record, profile, conf)
        cleaned.append(new_record)
    return cleaned
