'''
The purpose of the code in this file is to find and strip generic noise across a slug's records.
The noise can be one of or all of following: running headers/footers, page numbers.
It's supposed to report per-record structural confidence. 
'''

from dataclasses import dataclass
import re

EDGE_LINES = 3
LOW_CONF_THRESHOLD = 0.4
OFFSET_MIN_COVERAGE = 0.7
SPACING_RATIO = 0.15
REPEAT_THRESHOLD = 0.5
LOCAL_HEADER_MIN_RUN = 3

WS        = re.compile(r"\s+")      # whitespace runs
DOT_LEADER = re.compile(r"\.{3,}")  # 3+ consecutive dots
DIGITS    = re.compile(r"\d+")      # digit runs

DEFAULT_PAGE_NUM_PATTERNS = [
    re.compile(r"^\s*\d{1,4}\s*$"),          # bare int
    re.compile(r".*\s\d{1,4}\s*$"),           # title + trailing number
    re.compile(r"^\s*\d{1,4}\s+[A-Za-z]"),    # leading number + title (outer-margin pages)
]

@dataclass
class NoiseProfile:
    header_keys: set[str]           # Normalized signatures of edge lines appearing on >50% of records.
    footer_keys: set[str]           # Used to match headers/footers across pages, tolerant of changing numbers.
    offset: int | None              # Printed page = PDF page − offset
    offset_coverage: float          # Fraction of numbered records that support offset. Confidence in the offset.
    record_conf: list[float]        # How well the noise rules understood the page, not how good the content is.
                                    # Purpose: tells textNormalization whether to strip aggressively (high) or conservatively (low)
    review_flags: list[list[str]]   # Per-Record (e.g. "low_conf", "spacing")
    notes: list[str]                # Slug-level analysis summary, for humans/logging.
    exclude: list[bool]

def analyze(records, rules=None) -> NoiseProfile:
    '''
    Orchestrates everything: detect_repeated → infer_offset → per-record record_confidence/review_flags/exclude → notes.
    Prints the summary on stdout.
    '''
    # 1. Split for header and footer.
    edges = [get_header_footer(r["text"]) for r in records] 

    # 2. Identify noise
    header_keys, footer_keys = detect_repeated(edges)

    # 3. Infer offset
    offset, coverage = infer_offset(records, edges)

    # 4. Patterns (default + optional source overrides)
    patterns = DEFAULT_PAGE_NUM_PATTERNS + list(getattr(rules, "PAGE_PATTERNS", []))

    # 5. Make profile per record
    profile = NoiseProfile(
        header_keys=header_keys, footer_keys=footer_keys,
        offset=offset, offset_coverage=coverage,
        record_conf=[], review_flags=[], notes=[], exclude=[]
    )
    for record, (header, footer) in zip(records, edges):
        excluded = False
        conf = record_confidence(record, header, footer, profile)
        flags = review_flags(record, header, footer, profile, conf)
        if isinstance(record.get("page"), int):
            excluded = offset is not None and page_number(footer, patterns) != record["page"] - offset
        profile.record_conf.append(conf)
        profile.review_flags.append(flags)
        profile.exclude.append(excluded)

    profile.notes.append(f"offset={offset} coverage={coverage:.2f}")
    print("Records processed")
    return profile

def detect_local_headers(edges: list[tuple[list[str], list[str]]]) -> set[str]:
    '''
    Finds normalized first-lines that repeat across a run of consecutive
    records (running headers that vary by chapter/section, so they never
    cross the global REPEAT_THRESHOLD).
    '''
    keys: set[str] = set()
    run_key, run_len = None, 0

    def flush() -> None:
        nonlocal run_key, run_len
        if run_key is not None and run_len >= LOCAL_HEADER_MIN_RUN:
            keys.add(run_key)
        run_key, run_len = None, 0

    for header, _ in edges:
        key = noise_key(header[0]) if header else None
        if key is not None and key == run_key:
            run_len += 1
        else:
            flush()
            run_key, run_len = key, 1
    flush()
    return keys


def detect_repeated(edges: list[tuple[list[str], list[str]]]) -> tuple[set[str], set[str]]:
    '''
    detect_repeated finds boilerplate: the edge lines that occur across most pages (running headers, section footers). 
    A line that appears on >50% of a slug's records is noise, not content.
    Lets textNormalization know which lines to strip.
    '''
    total = 0
    header_count, footer_count = {}, {}
    for header, footer in edges:
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
    header_keys |= detect_local_headers(edges)
    footer_keys = {k for k, c in footer_count.items() if c / total > REPEAT_THRESHOLD}

    return (header_keys, footer_keys)

def get_header_footer(text: str, n: int = EDGE_LINES) -> tuple[list[str], list[str]]:
    '''
    Returns the header and footer of the given record.
    The header and footer is defined as EDGE_LINES # of lines from top and below.
    '''
    split_text = [l.strip() for l in text.splitlines() if l.strip()]
    header_candidates = split_text[:n]
    footer_candidates = split_text[-n:]
    return (header_candidates, footer_candidates)

def infer_offset(records: list[dict], edges: list[tuple[list[str], list[str]]]) -> tuple[int|None, float]:
    '''
    For each record, n = inferred_page_number; d = page - n;
    take the mode as offset, coverage = count(mode)/count(numbered). 
    Validate coverage ≥ 0.7 and roughly +1/page trend; return (None, coverage) if it fails.
    '''
    diff_count: dict[int, int] = {}
    numbered: list[tuple[int, int]] = []

    for record, (header, footer) in zip(records, edges):
        page = record.get("page")
        if not isinstance(page, int):
            continue

        printed_page_num = page_number(footer, DEFAULT_PAGE_NUM_PATTERNS)
        if printed_page_num is None:
            printed_page_num = page_number(header, DEFAULT_PAGE_NUM_PATTERNS)
        if printed_page_num is None:
            continue

        numbered.append((page, printed_page_num))
        diff = page - printed_page_num
        diff_count[diff] = diff_count.get(diff, 0) + 1

    if not numbered:
        return (None, 0.0)

    offset = max(diff_count, key=diff_count.get)
    coverage = diff_count[offset] / len(numbered)

    if coverage < OFFSET_MIN_COVERAGE:
        return (None, coverage)

    # printed numbers should advance in step with pdf pages (allowing gaps)
    numbered.sort(key=lambda pair: pair[0])
    steps = 0
    matches = 0
    for (page_a, printed_a), (page_b, printed_b) in zip(numbered, numbered[1:]):
        steps += 1
        if printed_b - printed_a == page_b - page_a:
            matches += 1
    monotonic = matches / steps if steps else 0.0
    if monotonic < OFFSET_MIN_COVERAGE:
        return (None, coverage)

    return (offset, coverage)

def noise_key(text:str) -> str:
    '''
    Remove the most basic noise so it becomes easier for the code to setup file for textNormalization.
    '''
    text = text.strip().lower()
    text = WS.sub(" ", text)              # collapse whitespace -> single space
    text = DOT_LEADER.sub(" ... ", text)  # collapse dot leaders -> fixed marker
    text = DIGITS.sub("#", text)          # digit -> #
    return text.strip(" .,:;-")           # trim edge punctuation

def page_number(lines: list[str], patterns: list[re.Pattern] | None = None) -> int | None:
    '''
    Uses the page-number regexes to find the page number.
    Returns the printed page integer if `line` is a page-number line, else None.
    '''
    for line in reversed(lines):
        if any(p.search(line) for p in (patterns or DEFAULT_PAGE_NUM_PATTERNS)):
            trailing = re.search(r"\d+\s*$", line)
            if trailing:
                return int(trailing.group())
            leading = re.match(r"\s*(\d{1,4})\s+[A-Za-z]", line)
            if leading:
                return int(leading.group(1))
    return None

def record_confidence(record: dict, header: list[str], footer: list[str], profile: NoiseProfile) -> float:
    '''
    Structural confidence (0-1): how many expected markers this page explained (repeated header present, footer number matches offset, no contradiction). 
    Tells textNormalization whether to strip aggressively.
    '''
    checks = passed = 0

    if profile.header_keys:
        checks += 1
        if any(noise_key(line) in profile.header_keys for line in header):
            passed += 1

    page = record.get("page")
    if profile.offset is not None and isinstance(page, int):
        checks += 1
        n = page_number(footer)
        if n is None:
            n = page_number(header)
        if n == page - profile.offset:
            passed += 1

    return 1.0 if checks == 0 else passed / checks

def single_letter_ratio(text):
    '''
    Returns the fraction of tokens that are single characters (after stripping
    '''
    toks = text.split()
    return sum(1 for t in toks if len(t.strip(".,;:()")) == 1) / len(toks) if toks else 0.0

def review_flags(record: dict, header: list[str], footer: list[str], profile: NoiseProfile, conf) -> list[str]:
    '''
    Human-review labels: low_conf, no_page_num, matter, spacing.
        - low_conf:     conf < LOW_CONF_THRESHOLD (e.g. 0.5).
        - no_page_num:  record["page"] is int but page_number(footer/header) is None.
        - spacing:      abnormal spacing.
        - matter:       non-body record.
    '''
    flags = []

    if conf < LOW_CONF_THRESHOLD:
        flags.append("low_conf")

    page = record.get("page")
    n = page_number(footer) or page_number(header)

    if isinstance(page, int) and n is None:
        flags.append("no_page_number")

    if isinstance(page, int) and profile.offset is not None and n != page - profile.offset:
        flags.append("matter")

    text = record["text"]
    if single_letter_ratio(text) > SPACING_RATIO:
        flags.append("spacing")

    return flags