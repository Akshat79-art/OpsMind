from noise_detection import LOW_CONF_THRESHOLD
from noise_detection import noise_key, page_number, NoiseProfile

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