'''
Drops records that are too thin to be useful (stubs, image-only sections, near-empty pages) using a per-slug prose-length cutoff.
'''

ABSOLUTE_FLOOR = 50
IQR_FACTOR = 1.5

def quantile_value(values: list[int], q: float) -> float:
    '''
    Returns the q-th quantile (0..1) of the values using linear interpolation between the two nearest ranks.
    '''
    if not values:
        return 0.0
    ordered = sorted(values)
    if len(ordered) == 1:
        return float(ordered[0])
    pos = q * (len(ordered) - 1)
    low = int(pos)
    high = min(low + 1, len(ordered) - 1)
    frac = pos - low
    return ordered[low] + (ordered[high] - ordered[low]) * frac


def compute_cutoff(lengths: list[int], floor: int = ABSOLUTE_FLOOR) -> float:
    '''
    Computes the per-slug cutoff as max(floor, Q1 - IQR_FACTOR * IQR).
    The floor protects small slugs from nonsense statistics.
    '''
    if not lengths:
        return float(floor)
    q1 = quantile(lengths, 0.25)
    q3 = quantile(lengths, 0.75)
    iqr = q3 - q1
    lower_fence = q1 - IQR_FACTOR * iqr
    return max(float(floor), lower_fence)


def filter_short_records(records: list[dict]) -> list[dict]:
    '''
    Drops records whose cleaned text length is below the per-slug cutoff.
    Returns the records that are long enough to be useful.
    '''
    lengths = [len(record["text"].strip()) for record in records]
    cutoff = compute_cutoff(lengths)
    return [record for record, length in zip(records, lengths) if length >= cutoff]
