'''
Chunks cleaned records into ~500-token windows with overlap and writes the result to chunks_data.
'''

import json
import os
from pathlib import Path

from dotenv import load_dotenv
from functools import lru_cache
from transformers import AutoTokenizer

load_dotenv(Path(__file__).resolve().parents[2] / ".env")

CHUNK_SIZE = 500
CHUNK_OVERLAP = 75
MODEL_NAME = os.getenv("MODEL_NAME")
STEP = CHUNK_SIZE - CHUNK_OVERLAP

INPUT_ROOT = Path("../../data/processedData")
OUTPUT_ROOT = Path("../../data/chunks_data")

@lru_cache(maxsize = 1)
def get_tokenizer():
    return AutoTokenizer.from_pretrained(MODEL_NAME)

def chunk_text(text: str) -> list[str]:
    '''
    Splits text into overlapping windows of CHUNK_SIZE tokens.
    Returns the original text slices (token offsets preserve case and punctuation).
    '''
    encoded = get_tokenizer(text, add_special_tokens=False, return_offsets_mapping=True)
    offsets = encoded["offset_mapping"]
    if not offsets:
        return []

    chunks = []
    for start in range(0, len(offsets), STEP):
        end = min(start + CHUNK_SIZE, len(offsets))
        char_start = offsets[start][0]
        char_end = offsets[end - 1][1]
        chunk = text[char_start:char_end].strip()
        if chunk:
            chunks.append(chunk)
        if end >= len(offsets):
            break
    return chunks


def chunk_records(records: list[dict]) -> list[dict]:
    '''
    Turns each record into one or more chunk records, adding chunk_index
    and a stable chunk_id.
    '''
    chunks = []
    for record in records:
        for index, text in enumerate(chunk_text(record["text"])):
            chunk = dict(record)
            chunk["chunk_index"] = index
            chunk["chunk_id"] = f"{record['category']}/{record['slug']}/{record['order']}/{index}"
            chunk["text"] = text
            chunks.append(chunk)
    return chunks


def main() -> None:

    total_chunks = 0

    for records_path in sorted(INPUT_ROOT.glob("*/*/records.jsonl")):
        category, slug, _ = records_path.relative_to(INPUT_ROOT).parts

        with open(records_path, "r", encoding="utf-8") as f:
            records = [json.loads(line) for line in f if line.strip()]

        chunks = chunk_records(records)

        out_path = OUTPUT_ROOT / category / slug / "chunks.jsonl"
        out_path.parent.mkdir(parents=True, exist_ok=True)
        with open(out_path, "w", encoding="utf-8") as f:
            for chunk in chunks:
                f.write(json.dumps(chunk, ensure_ascii=False) + "\n")

        total_chunks += len(chunks)
        print(f"{category}/{slug}: records={len(records)} chunks={len(chunks)}")

    print(f"\nDone. total chunks={total_chunks}")


if __name__ == "__main__":
    main()
