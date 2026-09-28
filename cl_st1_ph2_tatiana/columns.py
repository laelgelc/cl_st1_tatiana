#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path
from typing import Dict, List, Set


# === Configuration ===
KEYWORD_FILE = Path("corpus/04_top_labels/top_labels.txt")
TAGGED_BASE = Path("corpus/03_label_types")
OUTPUT_DIR = Path("columns")
CLEAN_DIR = Path("columns_clean")
INDEX_FILE = Path("index_top_labels.txt")
FILE_IDS = Path("file_ids.txt")  # <-- renamed


def main() -> int:
    # === Step 0: Basic validation of paths ===
    if not KEYWORD_FILE.exists():
        print(f"Error: keyword file not found: {KEYWORD_FILE}", file=sys.stderr)
        return 1
    if not TAGGED_BASE.exists():
        print(f"Error: tagged base directory does not exist: {TAGGED_BASE}", file=sys.stderr)
        return 1
    if not TAGGED_BASE.is_dir():
        print(f"Error: tagged base path is not a directory: {TAGGED_BASE}", file=sys.stderr)
        return 1

    # === Step 1: Load labels from KEYWORD_FILE ===
    try:
        raw_lemmas = [
            kw.strip()
            for kw in KEYWORD_FILE.read_text(encoding="utf-8").splitlines()
            if kw.strip()
        ]
    except OSError as exc:
        print(f"Error: failed to read keyword file {KEYWORD_FILE}: {exc}", file=sys.stderr)
        return 1

    if not raw_lemmas:
        print(f"Error: keyword file is empty (no non-empty lines): {KEYWORD_FILE}", file=sys.stderr)
        return 1

    # Ensure stable, duplicate-free label list
    lemmas: List[str] = sorted(set(raw_lemmas))

    # === Step 2: Create index map for unique labels (proper numbering) ===
    lemma_index: Dict[str, str] = {lemma: f"{i + 1:06d}" for i, lemma in enumerate(lemmas)}

    # === Step 3: Collect all label text files from TAGGED_BASE (flat directory) ===
    text_paths: List[Path] = sorted(
        p for p in TAGGED_BASE.iterdir() if p.is_file() and p.suffix == ".txt"
    )

    if not text_paths:
        print(
            f"Error: no .txt files found in tagged base directory: {TAGGED_BASE}",
            file=sys.stderr,
        )
        return 1

    # === Step 4: Assign file IDs and write FILE_IDS ===
    file_id_map: Dict[Path, str] = {}
    try:
        with FILE_IDS.open("w", encoding="utf-8") as fidx:
            for i, text_file in enumerate(text_paths, 1):
                fid = f"t{i:06d}"
                file_id_map[text_file] = fid
                # In a flat corpus, this is just the file name
                rel_name = text_file.name
                fidx.write(f"{fid} {rel_name}\n")
    except OSError as exc:
        print(f"Error: failed to write file IDs to {FILE_IDS}: {exc}", file=sys.stderr)
        return 1

    # === Step 5: Read each text and record label presence ===
    text_infos: List[Dict[str, object]] = []
    for text_file in text_paths:
        fid = file_id_map[text_file]

        present: Set[str] = set()
        try:
            with text_file.open("r", encoding="utf-8") as tf:
                for line in tf:
                    label = line.strip()
                    if label:
                        present.add(label)
        except OSError as exc:
            print(
                f"Warning: failed to read label file {text_file}: {exc}",
                file=sys.stderr,
            )
            continue

        text_infos.append(
            {
                "id": fid,
                "name": text_file.name,
                "labels": present,
            }
        )

    if not text_infos:
        print(
            "Error: all label files failed to read; no data available for column creation.",
            file=sys.stderr,
        )
        return 1

    # === Step 6: Write one column file per label ===
    try:
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    except OSError as exc:
        print(f"Error: failed to create output directory {OUTPUT_DIR}: {exc}", file=sys.stderr)
        return 1

    for lemma in lemmas:
        lemma_id = lemma_index[lemma]
        outpath = OUTPUT_DIR / f"{lemma_id}.txt"

        try:
            with outpath.open("w", encoding="utf-8") as outf:
                for info in text_infos:
                    labels: Set[str] = info["labels"]  # type: ignore[assignment]
                    has_kw = 1 if lemma in labels else 0
                    outf.write(f"{info['id']} {has_kw}\n")
        except OSError as exc:
            print(f"Error: failed to write column file {outpath}: {exc}", file=sys.stderr)
            return 1

    # === Step 7: Save label index (consistent with column filenames) ===
    try:
        with INDEX_FILE.open("w", encoding="utf-8") as idxf:
            for lemma in lemmas:
                idxf.write(f"{lemma_index[lemma]} {lemma}\n")
    except OSError as exc:
        print(f"Error: failed to write index file {INDEX_FILE}: {exc}", file=sys.stderr)
        return 1

    # === Step 8: Produce clean column files ===
    try:
        CLEAN_DIR.mkdir(parents=True, exist_ok=True)
    except OSError as exc:
        print(f"Error: failed to create clean directory {CLEAN_DIR}: {exc}", file=sys.stderr)
        return 1

    for lemma in lemmas:
        lemma_id = lemma_index[lemma]
        src = OUTPUT_DIR / f"{lemma_id}.txt"
        dst = CLEAN_DIR / f"{lemma_id}.txt"

        try:
            lines = src.read_text(encoding="utf-8").splitlines()
        except OSError as exc:
            print(f"Error: failed to read column file {src}: {exc}", file=sys.stderr)
            return 1

        try:
            with dst.open("w", encoding="utf-8") as fout:
                fout.write(f"{lemma_id}\n")
                for line in lines:
                    parts = line.split()
                    if parts:
                        # Last token is the binary presence flag
                        fout.write(f"{parts[-1]}\n")
        except OSError as exc:
            print(f"Error: failed to write clean column file {dst}: {exc}", file=sys.stderr)
            return 1

    print("Processing complete.")
    print(f"→ Columns in '{OUTPUT_DIR}/'")
    print(f"→ Clean binary columns in '{CLEAN_DIR}/'")
    print(f"→ File IDs saved to '{FILE_IDS}'")
    print(f"→ Label index saved to '{INDEX_FILE}'")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())