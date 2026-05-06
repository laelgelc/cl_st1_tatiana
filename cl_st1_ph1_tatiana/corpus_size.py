#!/usr/bin/env python3
"""
Compute simple corpus size statistics for corpus/03_label_types.

- Assumes each .txt file in corpus/03_label_types contains one label per non-empty line.
- Counts:
  - Number of files.
  - Number of labels (lines) overall.
  - Optionally: counts per "season" bucket derived from filename (tweet ID).

Output:
  corpus_size/corpus_size.tsv
"""

from __future__ import annotations

import re
from pathlib import Path
from collections import defaultdict

# --- CONFIGURATION ---
CORPUS_ROOT = Path("corpus/03_label_types")

# Example "season" extraction: use the middle numeric block in tweet IDs like
# tweet_000002_000001.txt -> season = "000002".
SEASON_PATTERN = re.compile(r"^tweet_(\d{6})_\d{6}$")

# --- GLOBAL COUNTERS ---
total_files = 0
total_labels = 0

# By season (optional)
file_counts_season: dict[str, int] = defaultdict(int)
label_counts_season: dict[str, int] = defaultdict(int)


def extract_season(filename_stem: str) -> str:
    """
    Extract a "season" bucket from the tweet filename stem.

    For names like 'tweet_000002_000001', returns '000002'.
    If the pattern does not match, returns 'unknown'.
    """
    m = SEASON_PATTERN.match(filename_stem)
    if m:
        return m.group(1)
    return "unknown"


def process_file(path: Path) -> None:
    """Count labels in a single label-types file."""
    global total_files, total_labels

    total_files += 1
    season = extract_season(path.stem)

    labels = 0
    with path.open(encoding="utf-8") as f:
        for line in f:
            if line.strip():
                labels += 1

    total_labels += labels
    file_counts_season[season] += 1
    label_counts_season[season] += labels


def main() -> int:
    if not CORPUS_ROOT.exists():
        print(f"Error: corpus root does not exist: {CORPUS_ROOT}")
        return 1
    if not CORPUS_ROOT.is_dir():
        print(f"Error: corpus root is not a directory: {CORPUS_ROOT}")
        return 1

    txt_files = sorted(p for p in CORPUS_ROOT.iterdir() if p.is_file() and p.suffix == ".txt")
    if not txt_files:
        print(f"Error: no .txt files found in {CORPUS_ROOT}")
        return 1

    for txt in txt_files:
        process_file(txt)

    out_dir = Path("corpus_size")
    out_dir.mkdir(exist_ok=True)
    out = out_dir / "corpus_size.tsv"

    with out.open("w", encoding="utf-8") as f:
        f.write("Strata\tFile Count\tLabel Count\n")

        # by season
        for ss in sorted(file_counts_season):
            f.write(f"{ss}\t{file_counts_season[ss]}\t{label_counts_season[ss]}\n")
        f.write("\n")

        # overall
        f.write(f"overall\t{total_files}\t{total_labels}\n")

    print(f"Corpus sizes saved to {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())