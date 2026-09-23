'''
Orchestrates the cleaning stage: reads every slug's extracted records,
detects noise, normalizes text, drops front/back matter and thin records,
and writes the result to processedData.
Run from app/cleaning_scripts.
'''

import json
from pathlib import Path

from noise_detection import analyze
from textNormalization import normalize_records
from prose_length_filter import filter_short_records

INPUT_ROOT = Path("../../data/extractedData")
OUTPUT_ROOT = Path("../../data/processedData")


def clean_data(input_root: Path = INPUT_ROOT, output_root: Path = OUTPUT_ROOT) -> None:
    '''
    Cleans every slug under input_root and writes processedData records.
    Prints a per-slug summary and a final total.
    '''
    total_read = total_written = 0

    for records_path in sorted(input_root.glob("*/*/records.jsonl")):
        category, slug, _ = records_path.relative_to(input_root).parts

        with open(records_path, "r", encoding="utf-8") as f:
            records = [json.loads(line) for line in f if line.strip()]

        profile = analyze(records, None)
        cleaned = normalize_records(records, profile)

        kept = [record for record, excluded in zip(cleaned, profile.exclude) if not excluded]
        kept = filter_short_records(kept)

        out_path = output_root / category / slug / "records.jsonl"
        out_path.parent.mkdir(parents=True, exist_ok=True)
        with open(out_path, "w", encoding="utf-8") as f:
            for record in kept:
                f.write(json.dumps(record, ensure_ascii=False) + "\n")

        excluded = sum(profile.exclude)
        short = len(cleaned) - excluded - len(kept)
        print(f"{category}/{slug}: read={len(records)} excluded={excluded} short={short} written={len(kept)}")

        total_read += len(records)
        total_written += len(kept)

    print(f"\nDone. read={total_read} written={total_written}")


if __name__ == "__main__":
    clean_data()
