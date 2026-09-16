'''
Scripts to turn raw markdowns to jsonl file.
'''

from collections.abc import Iterable
from pathlib import Path

import json
import os

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


def get_section_title(section: list[str]) -> str | None:
    for raw in section:
        s = raw.strip()
        if not s:
            continue
        if s.startswith(("![", "|", "-", "*")):   # image / table / bullet
            return None
        if s.startswith("#"):
            s = s.lstrip("#").strip()
        return s if len(s) <= 80 else None
    return None


def extractMD() -> None:
    totalFiles = 0
    totalFolders = 0

    for subfolder, filenames in find_subfolders_with_files(INPUT_ROOT):
        # Mirror this subfolder's relative path under the output root.

        order = 0
        md_files = [f for f in filenames if f.lower().endswith(".md")]

        if not md_files:
            continue

        rel_path = os.path.relpath(subfolder, INPUT_ROOT)
        output_subfolder = os.path.join(OUTPUT_ROOT, rel_path)
        os.makedirs(output_subfolder, exist_ok=True)

        print(f"[{subfolder}]  ->  [{output_subfolder}]  ({len(md_files)} files)")
        totalFolders += 1

        for filename in md_files:
            input_filepath = os.path.join(subfolder, filename)
            category, slug = get_category_slug(input_filepath, INPUT_ROOT)

            output_filepath = os.path.join(output_subfolder, "records.jsonl")

            # try block 1: opening input MD + output file
            try:
                with open(input_filepath, "r", encoding="utf-8") as f:
                    content = f.read()
                output_file = open(output_filepath, "w", encoding="utf-8")
            except Exception as e:
                print(f"[skip] {filename}: could not open file(s) due to: {e}")
                continue

            with output_file:

                # Parse the H1 title
                lines = content.splitlines()
                h1 = next((l.lstrip("# ").strip() for l in lines if l.startswith("# ")), None)

                sections, current = [], []
                for line in lines:
                    if line.strip() == "---":
                        sections.append(current)
                        current = []
                    else:
                        current.append(line)
                sections.append(current)

                for section in sections:
                    if not any(line.strip() for line in section):
                        continue

                    section_title = get_section_title(section)
                    if section_title and section_title != h1:
                        title = f"{h1} > {section_title}" if h1 else section_title
                    else:
                        title = h1 or section_title
                        
                    record = {
                        "category": category,
                        "slug": slug,
                        "source": filename,
                        "page": None,
                        "order": order,
                        "title": title,
                        "text": "\n".join(section)
                    }
                    output_file.write(json.dumps(record, ensure_ascii=False) + "\n")
                    order += 1

            totalFiles += 1
            print("Data extracted from this file.")

    print(f"\nDone. Processed {totalFiles} files across {totalFolders} subfolders.")
    print(f"Output written to: {os.path.abspath(OUTPUT_ROOT)}")


if __name__ == "__main__":
    extractMD()