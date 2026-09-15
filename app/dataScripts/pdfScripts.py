'''
Scripts to turn raw pdfs to jsonl file.
'''

from collections.abc import Iterable
from pathlib import Path

import json
import os
import pypdf

INPUT_ROOT = "../../data/rawData/"
OUTPUT_ROOT = "../../data/extractedData"


def find_subfolders_with_files(root_dir: str) -> Iterable[tuple[str, list[str]]]:
    """
    Yields (subfolder_path, [filenames]) for every subfolder under
    root_dir that directly contains at least one file.
    """
    for dirpath, _, filenames in os.walk(root_dir):
        if dirpath == root_dir:
            # Skip the root itself, only interested in its subfolders.
            continue
        if filenames:
            yield dirpath, sorted(filenames)


def get_category_slug(inputPath: Path, inputRoot: Path) -> tuple[str, str]:
    """
    e.g. get_category_slug(
            "/OpsMind/data/rawData/linux/TLCL/bookName.pdf",
        )
         -> ("linux", "TLCL")
    """
    inputPath = Path(inputPath)
    inputRoot = Path(inputRoot)
    path = inputPath.relative_to(inputRoot)
    category, slug, _ = path.parts
    return category, slug


def extractPDF() -> None:
    totalFiles = 0
    totalFolders = 0

    for subfolder, filenames in find_subfolders_with_files(INPUT_ROOT):
        # Mirror this subfolder's relative path under the output root.

        pdf_files = [f for f in filenames if f.lower().endswith(".pdf")]
        if not pdf_files:
            continue
        rel_path = os.path.relpath(subfolder, INPUT_ROOT)
        output_subfolder = os.path.join(OUTPUT_ROOT, rel_path)
        os.makedirs(output_subfolder, exist_ok=True)

        print(f"[{subfolder}]  ->  [{output_subfolder}]  ({len(pdf_files)} files)")
        totalFolders += 1

        for filename in pdf_files:
            input_filepath = os.path.join(subfolder, filename)
            category, slug = get_category_slug(input_filepath, INPUT_ROOT)

            output_filepath = os.path.join(output_subfolder, "records.jsonl")

            # try block 1: opening input PDF + output file
            try:
                pdfReader = pypdf.PdfReader(input_filepath)

                if pdfReader.is_encrypted:
                    if pdfReader.decrypt("") == pypdf.PasswordType.NOT_DECRYPTED:
                        print(f"[skip] {filename}: encrypted, cannot read with empty password")
                        continue

                output_file = open(output_filepath, "w", encoding="utf-8")
            except Exception as e:
                print(f"[skip] {filename}: could not open file(s): {e}")
                continue

            with output_file:
                for i, page in enumerate(pdfReader.pages, start=1):
                    # try block 2: extracting a single page
                    try:
                        text = page.extract_text()
                    except Exception as e:
                        print(f"[skip] {filename} page {i}: {e}")
                        continue

                    if not text or not text.strip():
                        continue

                    record = {
                        "category": category,
                        "slug": slug,
                        "source": filename,
                        "page": i,
                        "heading": None,
                        "order": i,
                        "title": None,
                        "text": text
                    }
                    output_file.write(json.dumps(record, ensure_ascii=False) + "\n")

                totalFiles += 1
                print("Data extracted from this file.")

    print(f"\nDone. Processed {totalFiles} files across {totalFolders} subfolders.")
    print(f"Output written to: {os.path.abspath(OUTPUT_ROOT)}")


if __name__ == "__main__":
    extractPDF()