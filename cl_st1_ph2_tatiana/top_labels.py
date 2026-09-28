#!/usr/bin/env python3
"""Aggregate label frequencies from label files and write top-label reports.

Overview
========
This script scans an input directory containing text files with labels, counts how
often each label occurs across all files, and writes two summary files:

* ``top_labels_counts.txt`` – all distinct labels with their total counts, one per line:

  ``<label> <count>``

  Lines are sorted in descending order of ``count`` and then by label as a
  tie-breaker for deterministic output.

* ``top_labels.txt`` – the first 1,000 labels from the same sorted list, but **without**
  counts, one label per line. If there are fewer than 1,000 labels, all labels are
  written.

Typical Usage
=============
Run from the project root:

.. code-block:: bash

   python top_labels.py \
       --input-dir corpus/03_label_types \
       --output-dir corpus/04_top_labels

Command-Line Interface
======================
Required arguments:

* ``--input-dir DIR``

  Directory containing the label files to be aggregated. The script reads all relevant
  files under this directory (``*.txt`` files, non-recursively) and extracts labels
  from them.

* ``--output-dir DIR``

  Directory where the output files will be written:
  ``top_labels_counts.txt`` and ``top_labels.txt``. The directory is created if it
  does not already exist. Existing files with these names may be overwritten.

Processing Summary
==================
1. Discover and read all ``*.txt`` label files from ``--input-dir`` (non-recursively).
2. Parse labels from each file (one label per line, ignoring empty lines and surrounding
   whitespace).
3. Maintain a global counter ``label -> total occurrences`` across all files.
4. Sort labels primarily by descending count, and secondarily by label name as a
   deterministic tie-breaker.
5. Write the full sorted list with counts to ``top_labels_counts.txt``.
6. Write the first 1,000 labels (or fewer, if not enough labels) without counts to
   ``top_labels.txt``.
"""

from __future__ import annotations

import argparse
import sys
from collections import Counter
from pathlib import Path
from typing import Iterable, List, Tuple

MAX_TOP_LABELS = 1000
COUNTS_FILENAME = "top_labels_counts.txt"
TOP_LABELS_FILENAME = "top_labels.txt"


def parse_args(argv: Iterable[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Aggregate label frequencies from text label files and write "
            "top-label summary reports."
        )
    )
    parser.add_argument(
        "--input-dir",
        required=True,
        type=Path,
        help="Directory containing input *.txt label files.",
    )
    parser.add_argument(
        "--output-dir",
        required=True,
        type=Path,
        help="Directory where top_labels_counts.txt and top_labels.txt will be written.",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Print progress information to stderr.",
    )
    return parser.parse_args(list(argv) if argv is not None else None)


def find_label_files(input_dir: Path) -> List[Path]:
    """
    Return a sorted list of *.txt files directly under input_dir.

    Raises FileNotFoundError or NotADirectoryError if input_dir is invalid.
    """
    if not input_dir.exists():
        raise FileNotFoundError(f"Input directory does not exist: {input_dir}")
    if not input_dir.is_dir():
        raise NotADirectoryError(f"Input path is not a directory: {input_dir}")

    return sorted(
        p for p in input_dir.iterdir() if p.is_file() and p.suffix == ".txt"
    )


def count_labels(label_files: Iterable[Path]) -> Counter[str]:
    """
    Read labels from the given files and return a Counter mapping label -> count.

    Each non-empty line (after stripping whitespace) is treated as one label.
    """
    counts: Counter[str] = Counter()

    for path in label_files:
        try:
            with path.open("r", encoding="utf-8") as f:
                for line in f:
                    label = line.strip()
                    if not label:
                        continue
                    counts[label] += 1
        except OSError as exc:  # noqa: BLE001
            # Non-fatal: skip unreadable files but continue processing others.
            print(
                f"Warning: failed to read {path}: {exc}",
                file=sys.stderr,
            )
            continue

    return counts


def sort_label_counts(counts: Counter[str]) -> List[Tuple[str, int]]:
    """
    Return a list of (label, count) pairs sorted by:

      1. Descending count
      2. Ascending label (lexicographically) for deterministic ordering
    """
    return sorted(counts.items(), key=lambda item: (-item[1], item[0]))


def write_top_labels_counts(
        sorted_label_counts: List[Tuple[str, int]],
        output_path: Path,
) -> None:
    """
    Write all labels and their counts to output_path, one per line:

        <label> <count>
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as f:
        for label, count in sorted_label_counts:
            f.write(f"{label} {count}\n")


def write_top_labels(
        sorted_label_counts: List[Tuple[str, int]],
        output_path: Path,
        max_labels: int = MAX_TOP_LABELS,
) -> None:
    """
    Write up to max_labels labels (without counts) to output_path, one per line.

    Labels are taken in the order provided by sorted_label_counts.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as f:
        for label, _ in sorted_label_counts[:max_labels]:
            f.write(f"{label}\n")


def main(argv: Iterable[str] | None = None) -> int:
    args = parse_args(argv)

    try:
        label_files = find_label_files(args.input_dir)
    except (FileNotFoundError, NotADirectoryError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    if not label_files:
        # No label files: create empty outputs and exit successfully with a warning.
        print(
            f"Warning: no *.txt label files found in {args.input_dir}. "
            "Writing empty output files.",
            file=sys.stderr,
        )
        args.output_dir.mkdir(parents=True, exist_ok=True)
        (args.output_dir / COUNTS_FILENAME).write_text("", encoding="utf-8")
        (args.output_dir / TOP_LABELS_FILENAME).write_text("", encoding="utf-8")
        return 0

    if args.verbose:
        print(
            f"Found {len(label_files)} label files in {args.input_dir}",
            file=sys.stderr,
        )

    counts = count_labels(label_files)
    sorted_label_counts = sort_label_counts(counts)

    if args.verbose:
        print(
            f"Aggregated {len(sorted_label_counts)} distinct labels.",
            file=sys.stderr,
        )

    args.output_dir.mkdir(parents=True, exist_ok=True)
    counts_path = args.output_dir / COUNTS_FILENAME
    top_labels_path = args.output_dir / TOP_LABELS_FILENAME

    try:
        write_top_labels_counts(sorted_label_counts, counts_path)
        write_top_labels(sorted_label_counts, top_labels_path, max_labels=MAX_TOP_LABELS)
    except OSError as exc:  # noqa: BLE001
        print(f"Error writing output files: {exc}", file=sys.stderr)
        return 1

    if args.verbose:
        print(
            f"Wrote {counts_path.name} and {top_labels_path.name} to {args.output_dir}",
            file=sys.stderr,
        )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())