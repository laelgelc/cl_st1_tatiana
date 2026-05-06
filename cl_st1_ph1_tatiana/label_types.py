"""
Extract unique label descriptions from Google Cloud Vision JSON responses
and write them as simple text lists.

For each input JSON file, this script writes a .txt file with one
underscore-separated label per line.

Usage:
    python label_types.py --input-dir <INPUT_DIR> --output-dir <OUTPUT_DIR>

Example:
    python label_types.py \
        --input-dir corpus/02_labelled \
        --output-dir corpus/03_label_types
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Iterable, List, Set


def parse_args(argv: Iterable[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Convert Google Vision label annotations in JSON files to per-file "
            "lists of unique, underscore-separated label descriptions."
        )
    )
    parser.add_argument(
        "--input-dir",
        required=True,
        type=Path,
        help="Directory containing input *.json files.",
    )
    parser.add_argument(
        "--output-dir",
        required=True,
        type=Path,
        help="Directory where corresponding *.txt files will be written.",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Print progress information to stderr.",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Allow overwriting of existing output .txt files.",
    )
    return parser.parse_args(list(argv) if argv is not None else None)


def find_json_files(input_dir: Path) -> List[Path]:
    if not input_dir.exists():
        raise FileNotFoundError(f"Input directory does not exist: {input_dir}")
    if not input_dir.is_dir():
        raise NotADirectoryError(f"Input path is not a directory: {input_dir}")
    return sorted(p for p in input_dir.iterdir() if p.is_file() and p.name.endswith(".json"))


def extract_unique_descriptions(json_path: Path) -> List[str]:
    """
    Extract unique label descriptions from a single Vision API JSON file.

    Returns descriptions in order of first appearance, deduplicated
    case-sensitively.
    """
    try:
        with json_path.open("r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as exc:  # noqa: BLE001
        raise ValueError(f"Failed to parse JSON from {json_path}: {exc}") from exc

    responses = data.get("responses")
    if not isinstance(responses, list):
        return []

    seen: Set[str] = set()
    ordered: List[str] = []

    for resp in responses:
        if not isinstance(resp, dict):
            continue
        label_annotations = resp.get("labelAnnotations")
        if not isinstance(label_annotations, list):
            continue

        for label in label_annotations:
            if not isinstance(label, dict):
                continue
            desc = label.get("description")
            if not isinstance(desc, str):
                continue
            if desc in seen:
                continue
            seen.add(desc)
            ordered.append(desc)

    return ordered


def transform_description(desc: str) -> str:
    """
    Apply the required transformation to a label description.

    Currently: replace spaces with underscores.
    """
    return desc.replace(" ", "_")


def write_labels_txt(
        descriptions: List[str],
        output_path: Path,
        force: bool = False,
) -> None:
    """
    Write transformed descriptions (one per line) to the given path.

    If the file exists and force is False, it is silently overwritten
    (per the simple-behavior proposal in the specification).
    """
    # At the moment, 'force' does not change behavior and we always overwrite.
    # It is accepted for future extensibility.
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with output_path.open("w", encoding="utf-8") as f:
        for desc in descriptions:
            line = transform_description(desc)
            f.write(line + "\n")


def main(argv: Iterable[str] | None = None) -> int:
    args = parse_args(argv)

    try:
        json_files = find_json_files(args.input_dir)
    except (FileNotFoundError, NotADirectoryError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    if not json_files:
        print(f"No JSON files found in {args.input_dir}", file=sys.stderr)
        return 1

    if args.verbose:
        print(f"Found {len(json_files)} JSON files in {args.input_dir}", file=sys.stderr)

    args.output_dir.mkdir(parents=True, exist_ok=True)

    had_error = False
    processed_count = 0

    for json_path in json_files:
        try:
            descriptions = extract_unique_descriptions(json_path)
        except ValueError as exc:
            print(f"Error: {exc}", file=sys.stderr)
            had_error = True
            continue

        output_name = json_path.with_suffix(".txt").name
        output_path = args.output_dir / output_name

        try:
            write_labels_txt(descriptions, output_path, force=args.force)
        except OSError as exc:  # noqa: BLE001
            print(f"Error writing {output_path}: {exc}", file=sys.stderr)
            had_error = True
            continue

        processed_count += 1
        if args.verbose:
            print(
                f"Processing {json_path.name} -> {output_name} "
                f"({len(descriptions)} unique labels)",
                file=sys.stderr,
            )

    if args.verbose:
        print(f"Done. Processed {processed_count} files.", file=sys.stderr)

    return 1 if had_error else 0


if __name__ == "__main__":
    raise SystemExit(main())