'''
The purpose of the code in this file is to find and strip generic noise across a slug's records.
The noise can be one of or all of following: running headers/footers, page numbers.
It's supposed to report per-record structural confidence. 
'''

from dataclasses import dataclass
import re

EDGE_LINES = 3
REPEAT_THRESHOLD = 0.5
OFFSET_MIN_COVERAGE = 0.7

WS        = re.compile(r"\s+")      # whitespace runs
DOT_LEADER = re.compile(r"\.{3,}")  # 3+ consecutive dots
DIGITS    = re.compile(r"\d+")      # digit runs


@dataclass
class NoiseProfile:
    header_keys: set[str]           # Normalized signatures of edge lines appearing on >50% of records.
    footer_keys: set[str]           # Used to match headers/footers across pages, tolerant of changing numbers.
    page_patterns: list[re.Pattern] # Regex that identify a page-number line: bare int, roman, or title + number.
    offset: int | None              # Printed page = PDF page − offset
    offset_coverage: float          # Fraction of numbered records that support offset. Confidence in the offset.
    record_conf: list[float]        # How well the noise rules understood the page, not how good the content is.
                                    # Purpose: tells textNormalization whether to strip aggressively (high) or conservatively (low)
    review_flags: list[list[str]]   # Per-Record (e.g. "low_conf", "spacing")
    notes: list[str]                # Slug-level analysis summary, for humans/logging.
    exclude: list[bool]


def get_header_footer(text: str, n: int = EDGE_LINES) -> tuple[list[str], list[str]]:
    '''
    Returns the header and footer of the given record.
    The header and footer is defined as EDGE_LINES # of lines from top and below.
    '''
    split_text = [l.strip() for l in text.splitlines() if l.strip()]
    header_candidates = split_text[:n]
    footer_candidates = split_text[-n:]
    # print(header_candidates, footer_candidates)
    return (header_candidates, footer_candidates)

def noise_key(text:str) -> str:
    '''
    Remove the most basic noise so it becomes easier for the code to setup file for textNormalization.
    '''
    text = text.strip().lower()
    text = WS.sub(" ", text)              # collapse whitespace -> single space
    text = DOT_LEADER.sub(" ... ", text)  # collapse dot leaders -> fixed marker
    text = DIGITS.sub("#", text)          # digit -> #
    # print("Noise removed text:")
    # print(text)
    return text.strip(" .,:;-")           # trim edge punctuation
    
def trailing_int(lines: list[str]) -> int | None:
    '''
    Infer the printed page number.
    '''
    if not lines:
        return None
    for line in reversed(lines):
        match = re.search(r"\d+\s*$", line)
        if match:
            return int(match.group())
    return None

def detect_repeated(records: list[dict]) -> tuple[set[str], set[str]]:
    '''
    detect_repeated finds boilerplate: the edge lines that recur across most pages (running headers, section footers). 
    A line that appears on >50% of a slug's records is noise, not content.
    Lets textNormalization know which lines to strip.
    '''
    total = 0
    header_count, footer_count = {}, {}
    for record in records:
        header, footer = get_header_footer(record["text"])
        for line in header:
            key = noise_key(line)
            header_count[key] = header_count.get(key, 0) + 1
        for line in footer:
            key = noise_key(line)
            footer_count[key] = footer_count.get(key, 0) + 1
        total += 1

    if total == 0:
        return (set(), set())
    
    header_keys = {k for k, c in header_count.items() if c / total > REPEAT_THRESHOLD}
    footer_keys = {k for k, c in footer_count.items() if c / total > REPEAT_THRESHOLD}

    return (header_keys, footer_keys)