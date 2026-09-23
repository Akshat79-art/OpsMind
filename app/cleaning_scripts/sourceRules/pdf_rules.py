'''
PDF source rules.

PAGE_PATTERNS describe the shape of a page-number line using placeholders:
    {n}     -> the printed page number (digits)
    {text}  -> surrounding text
They are compiled into regexes by noise_detection.compile_page_patterns.
'''

PAGE_PATTERNS = [
    "{n}",          # bare page number:        "137"
    "{text} {n}",   # title + trailing number: "5.1. Principles 137"
    "{n} {text}",   # leading number + title:  "44 Chapter 3. The application Layer"
]
