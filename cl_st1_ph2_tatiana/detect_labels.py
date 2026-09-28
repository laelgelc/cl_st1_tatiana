#!/usr/bin/env python3
"""
Command-line tool for running Google Cloud Vision LABEL_DETECTION on local images.

Overview
========
This script recursively scans one or more input directories for image files, calls the
Google Cloud Vision API with LABEL_DETECTION for each image, and writes the raw JSON
response for each image to disk:

* One JSON file per input image.
* The output directory structure mirrors the input directory structure.
* JSON file name shares the same base name as the image, with a `.json` extension.
* Supports:
  - Skipping already processed images (default).
  - Forced reprocessing via `--force`.
  - Parallel workers via `--workers`.
  - Test mode (`--test N`) to process only the first N images.
  - Dry-run mode (`--dry-run`) that plans work but does not call the API or write files.
  - Logging with configurable log level.

Authentication & Configuration
==============================
The script uses Google Cloud Application Default Credentials (ADC) via a *service account
JSON key*. The primary requirement is a valid service account key referenced by the
`GOOGLE_APPLICATION_CREDENTIALS` environment variable.

* **GOOGLE_APPLICATION_CREDENTIALS** (required)
  - Must point to a service account JSON key file.
  - The service account must have permission to call the Vision API on the intended project.

* **GOOGLE_CLOUD_PROJECT** (optional)
  - If set, it provides an explicit project ID.
  - If not set, the client uses the project configured in the service account key.

By default, the script expects to load a `.env` file at `env/.env` and populate
environment variables from there. A typical `.env` file might look like:

.. code-block:: text

   GOOGLE_APPLICATION_CREDENTIALS=/full/path/to/env/cl-st1-tatiana-92dcc00bf399.json
   GOOGLE_CLOUD_PROJECT=cl-st1-tatiana

`.env` Loading Rules
--------------------
1. The path to the `.env` file is:
   * Provided explicitly via `--env-file`, or
   * Defaults to `env/.env` (relative to the current working directory).

2. If the `.env` file exists:
   * Each non-empty, non-comment line of the form `KEY=VALUE` is parsed.
   * For each pair, `os.environ[KEY] = VALUE` is set (overwriting any existing value).

3. If the `.env` file does **not** exist:
   * A WARNING is logged.
   * The script assumes required environment variables may be set externally.

4. After `.env` loading:
   * If `GOOGLE_APPLICATION_CREDENTIALS` is **not** set:
     - An ERROR is logged explaining that credentials are required and how to set them.
     - The script exits with a non-zero status code.
   * `GOOGLE_CLOUD_PROJECT` is **optional**; if it is set, it is used, otherwise the
     client relies on the project encoded in the service account.

Vision Client Initialization
----------------------------
After loading configuration and validating that `GOOGLE_APPLICATION_CREDENTIALS` is
present, the script initializes a Google Cloud Vision client using ADC.

* If `GOOGLE_CLOUD_PROJECT` is set, it is passed as the `project` when appropriate.
* If client initialization fails, an ERROR is logged and the script exits non-zero.
* In **dry-run mode** (`--dry-run`), the Vision client is **not** initialized because
  no actual API calls are made.

Command-Line Interface
======================
All arguments are implemented using `argparse`.

Required Arguments
------------------
* ``--input-dir DIR`` (required, repeatable)

  One or more directories containing images. Each directory is:

  * Recursively scanned for image files.
  * Can be specified multiple times:

    .. code-block:: bash

       --input-dir images --input-dir more_images

* ``--output-dir DIR`` (required)

  Root directory where JSON output files are stored. The script creates this directory
  and any required subdirectories if they do not already exist.

Optional Arguments
------------------
* ``--env-file PATH`` (default: ``env/.env``)

  Path to the `.env` file used to set environment variables such as
  `GOOGLE_APPLICATION_CREDENTIALS` and `GOOGLE_CLOUD_PROJECT`.

* ``--max-results N`` (default: 50)

  Maximum number of labels requested per image for LABEL_DETECTION.

* ``--extensions EXT1,EXT2,...``

  Comma-separated list of allowed image file extensions, case-insensitive.
  Defaults to:

  * .jpg
  * .jpeg
  * .png
  * .gif
  * .bmp
  * .tiff

* ``--test N``

  Test mode: after discovering images and skipping existing outputs (unless `--force`
  is set), the remaining images are sorted deterministically and only the first N
  are processed. N must be a positive integer.

* ``--dry-run``

  Flag that performs all discovery and planning but **does not**:

  * Call the Vision API.
  * Read image files.
  * Write any JSON files.

  Instead, it logs which images **would** be processed and where their outputs would
  be written.

* ``--workers N`` (default: 1)

  Number of worker threads used for parallel processing:

  * `1` means sequential processing.
  * `N > 1` uses a thread pool to process images in parallel.

* ``--force``

  Flag that forces reprocessing of all images:

  * When not set (default), images that already have an existing JSON output are
    skipped.
  * When set, existing JSON outputs are ignored and all images are reprocessed.

* ``--log-level LEVEL`` (default: ``INFO``)

  Log level, one of: `DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL`.

Usage Examples
==============
Basic run:

.. code-block:: bash

   python detect_labels.py \
       --input-dir images \
       --output-dir vision_output

Multiple input directories:

.. code-block:: bash

   python detect_labels.py \
       --input-dir images \
       --input-dir more_images \
       --output-dir vision_output

Test mode (first N images):

.. code-block:: bash

   python detect_labels.py \
       --input-dir images \
       --output-dir vision_output \
       --test 20

Dry run (no Vision calls, no files written):

.. code-block:: bash

   python detect_labels.py \
       --input-dir images \
       --output-dir vision_output \
       --dry-run

With multiple workers:

.. code-block:: bash

   python detect_labels.py \
       --input-dir images \
       --output-dir vision_output \
       --workers 4

Force reprocessing of all images:

.. code-block:: bash

   python detect_labels.py \
       --input-dir images \
       --output-dir vision_output \
       --force

Processing Steps (Summary)
==========================
1. Parse command-line arguments.
2. Configure logging based on `--log-level`.
3. Load `.env` (default: `env/.env`) and populate environment variables.
4. Validate presence of `GOOGLE_APPLICATION_CREDENTIALS`.
5. Discover candidate images from one or more `--input-dir` directories.
6. Compute output JSON paths under `--output-dir` mirroring the input directory
   structure; skip existing outputs unless `--force` is set.
7. If `--test` is given, limit the images to the first N after sorting.
8. If `--dry-run` is set:
   * Log all planned input→output mappings.
   * Exit without API calls or file writes.
9. Otherwise:
   * Initialize the Vision client.
   * Process images sequentially or in parallel (`--workers`).
   * For each image: read bytes → call LABEL_DETECTION with retries →
     serialize response to JSON → write to output path.
10. Log a final summary (success, skipped, failed).

Logging Behavior
================
The script uses Python’s standard `logging` module.

* Logging is configured in `main()` with a simple format::

    [%(levelname)s] %(message)s

* `--log-level` controls verbosity.

Expected log output includes:

* INFO:
  - Number of input directories.
  - Number of candidate images discovered.
  - Number of images remaining after skip-existing filtering.
  - Whether test mode is enabled (and N).
  - Whether dry-run is enabled.
  - Periodic progress updates during processing.
  - Final summary (counts of successes, skips, failures).

* DEBUG:
  - Detailed per-image actions (e.g. “Skipping because JSON exists: ...”).
  - Additional diagnostics if needed.

* WARNING:
  - Non-fatal problems such as unreadable files.

* ERROR:
  - Fatal setup issues (e.g. missing `GOOGLE_APPLICATION_CREDENTIALS`).
  - Unrecoverable Vision API failures for specific images after retries.
  - JSON write failures.

On fatal configuration problems, the script exits with a non-zero status code.
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List, Optional, Sequence, Set, Tuple

from google.api_core import exceptions as gcloud_exceptions
from google.cloud import vision
from google.protobuf.json_format import MessageToDict


DEFAULT_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".bmp", ".tiff"}
DEFAULT_MAX_RESULTS = 50
DEFAULT_ENV_FILE = "env/.env"


@dataclass
class ImageTask:
    """Container tying an input image to its output JSON path."""
    image_path: Path
    output_path: Path


@dataclass
class ProcessResult:
    image_path: Path
    output_path: Path
    success: bool
    error: Optional[str] = None


def load_env(env_path: Path, logger: logging.Logger) -> None:
    """
    Load environment variables from a .env file if it exists.

    Each non-empty, non-comment line of form KEY=VALUE is added to os.environ.
    """
    if not env_path.exists():
        logger.warning("No .env file found at %s; relying on existing environment.", env_path)
        return

    logger.info("Loading environment variables from %s", env_path)
    try:
        with env_path.open("r", encoding="utf-8") as f:
            for raw_line in f:
                line = raw_line.strip()
                if not line or line.startswith("#"):
                    continue
                if "=" not in line:
                    logger.debug("Skipping invalid .env line (no '='): %s", line)
                    continue
                key, value = line.split("=", 1)
                key = key.strip()
                value = value.strip()
                if not key:
                    continue
                os.environ[key] = value
                logger.debug("Set env var from .env: %s=***", key)
    except OSError as exc:
        logger.error("Failed to read .env file %s: %s", env_path, exc)
        # Do not exit; environment may still be valid.


def validate_credentials(logger: logging.Logger) -> Optional[str]:
    """
    Ensure GOOGLE_APPLICATION_CREDENTIALS is present; return project ID (may be None).
    """
    creds = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS")
    if not creds:
        logger.error(
            "GOOGLE_APPLICATION_CREDENTIALS is not set. Please provide a service "
            "account JSON key, e.g. via env/.env:\n"
            "  GOOGLE_APPLICATION_CREDENTIALS=/full/path/to/key.json\n"
            "Optionally set GOOGLE_CLOUD_PROJECT to specify the project explicitly."
        )
        return None

    project_id = os.environ.get("GOOGLE_CLOUD_PROJECT")
    if project_id:
        logger.info("Using explicit Google Cloud project: %s", project_id)
    else:
        logger.info(
            "GOOGLE_CLOUD_PROJECT is not set; the Vision client will use the project "
            "encoded in the service account."
        )
    return project_id


def init_vision_client(project_id: Optional[str], logger: logging.Logger) -> vision.ImageAnnotatorClient:
    """
    Initialize and return a Google Cloud Vision ImageAnnotatorClient.

    If project_id is provided, it may be used for project-scoped configuration in calls.
    """
    try:
        client = vision.ImageAnnotatorClient()
        logger.debug("Successfully initialized Google Cloud Vision client.")
        return client
    except Exception as exc:  # noqa: BLE001
        logger.error("Failed to initialize Google Cloud Vision client: %s", exc)
        raise


def find_images(input_dirs: Sequence[Path], extensions: Set[str], logger: logging.Logger) -> List[Path]:
    """
    Recursively discover image files under the given input directories.

    Returns a list of absolute Paths.
    """
    images: List[Path] = []
    for root in input_dirs:
        if not root.exists():
            logger.warning("Input directory does not exist and will be skipped: %s", root)
            continue
        if not root.is_dir():
            logger.warning("Input path is not a directory and will be skipped: %s", root)
            continue
        logger.debug("Scanning input directory: %s", root)
        for path in root.rglob("*"):
            if not path.is_file():
                continue
            ext = path.suffix.lower()
            if ext in extensions:
                images.append(path.resolve())
                logger.debug("Discovered image: %s", path)
    logger.info("Discovered %d candidate images.", len(images))
    return images


def compute_output_path(
        image_path: Path,
        input_dirs: Sequence[Path],
        output_root: Path,
) -> Path:
    """
    Compute the output JSON path for an image.

    Finds the input_dir that is an ancestor of image_path and computes the
    relative path under that root. Returns output_root / relative.with_suffix(".json").
    """
    image_path_resolved = image_path.resolve()

    for root in input_dirs:
        root_resolved = root.resolve()
        try:
            relative = image_path_resolved.relative_to(root_resolved)
        except ValueError:
            continue
        # Found the root this image belongs to.
        json_relative = relative.with_suffix(".json")
        return output_root.joinpath(json_relative)

    # Fallback: if no root matched, just use the basename under output_root.
    json_name = image_path_resolved.name
    json_name = Path(json_name).with_suffix(".json").name
    return output_root / json_name


def build_tasks(
        images: Sequence[Path],
        input_dirs: Sequence[Path],
        output_root: Path,
        force: bool,
        logger: logging.Logger,
) -> Tuple[List[ImageTask], int]:
    """
    Build ImageTask objects for images and skip those with existing outputs unless force=True.

    Returns (tasks, skipped_count).
    """
    tasks: List[ImageTask] = []
    skipped_existing = 0

    for img in images:
        out_path = compute_output_path(img, input_dirs, output_root)
        if not force and out_path.exists():
            skipped_existing += 1
            logger.debug("Skipping (output already exists): %s -> %s", img, out_path)
            continue
        tasks.append(ImageTask(image_path=img, output_path=out_path))

    logger.info(
        "After skipping existing outputs (force=%s), %d images remain to process "
        "(%d skipped).",
        force,
        len(tasks),
        skipped_existing,
    )
    return tasks, skipped_existing


def apply_test_limit(tasks: List[ImageTask], limit: Optional[int], logger: logging.Logger) -> List[ImageTask]:
    """
    If limit is provided, sort tasks by image path and return only the first N.
    """
    if limit is None:
        return tasks

    if limit <= 0:
        raise ValueError("--test N must be a positive integer.")

    tasks_sorted = sorted(tasks, key=lambda t: str(t.image_path))
    limited = tasks_sorted[:limit]
    logger.info(
        "Test mode enabled: limiting processing to first %d images (of %d available).",
        len(limited),
        len(tasks_sorted),
    )
    return limited


def is_transient_error(exc: Exception) -> bool:
    """
    Heuristic to decide whether an API error is transient and worth retrying.
    """
    if isinstance(
            exc,
            (
                    gcloud_exceptions.DeadlineExceeded,
                    gcloud_exceptions.ServiceUnavailable,
                    gcloud_exceptions.InternalServerError,
                    gcloud_exceptions.TooManyRequests,
            ),
    ):
        return True

    code = getattr(exc, "code", None)
    if code in (429, 500, 502, 503, 504):
        return True

    return False


def call_vision_label_detection(
        client: vision.ImageAnnotatorClient,
        image_bytes: bytes,
        max_results: int,
        project_id: Optional[str],
) -> dict:
    """
    Call Vision LABEL_DETECTION and return a plain dict representation of the response.
    """
    image = vision.Image(content=image_bytes)
    features = [vision.Feature(type_=vision.Feature.Type.LABEL_DETECTION, max_results=max_results)]
    request = vision.AnnotateImageRequest(image=image, features=features)
    requests = [request]

    kwargs = {}
    if project_id:
        # The client typically infers project from credentials; explicit project may be used
        # via `request.project_id` in newer APIs. For backward compatibility, we keep it simple.
        pass

    response = client.batch_annotate_images(requests=requests, **kwargs)
    # response is BatchAnnotateImagesResponse
    try:
        # Prefer to_dict() if available.
        return response.to_dict()  # type: ignore[no-any-return]
    except AttributeError:
        return MessageToDict(response._pb)  # type: ignore[attr-defined]


def ensure_parent_dir(path: Path) -> None:
    """Ensure that the parent directory for a path exists."""
    parent = path.parent
    parent.mkdir(parents=True, exist_ok=True)


def process_single_image(
        client: vision.ImageAnnotatorClient,
        task: ImageTask,
        max_results: int,
        project_id: Optional[str],
        logger: logging.Logger,
        max_attempts: int = 3,
        initial_backoff: float = 1.0,
) -> ProcessResult:
    """
    Read an image, call Vision LABEL_DETECTION with retries, and write JSON output.
    """
    logger.debug("Processing image: %s -> %s", task.image_path, task.output_path)

    try:
        image_bytes = task.image_path.read_bytes()
    except OSError as exc:
        msg = f"Failed to read image file: {exc}"
        logger.warning("%s: %s", msg, task.image_path)
        return ProcessResult(task.image_path, task.output_path, success=False, error=msg)

    attempt = 0
    last_exc: Optional[Exception] = None
    while attempt < max_attempts:
        attempt += 1
        try:
            response_dict = call_vision_label_detection(
                client=client,
                image_bytes=image_bytes,
                max_results=max_results,
                project_id=project_id,
            )
            break
        except Exception as exc:  # noqa: BLE001
            last_exc = exc
            if not is_transient_error(exc) or attempt >= max_attempts:
                logger.error(
                    "Vision API call failed for %s (attempt %d/%d): %s",
                    task.image_path,
                    attempt,
                    max_attempts,
                    exc,
                )
                return ProcessResult(
                    task.image_path,
                    task.output_path,
                    success=False,
                    error=f"Vision API failed after {attempt} attempts: {exc}",
                )
            backoff = initial_backoff * (2 ** (attempt - 1))
            logger.warning(
                "Transient Vision API error for %s (attempt %d/%d): %s; retrying in %.1fs",
                task.image_path,
                attempt,
                max_attempts,
                exc,
                backoff,
            )
            time.sleep(backoff)
    else:
        # Should not reach here because we return on final failure above.
        msg = f"Vision API failed after {max_attempts} attempts: {last_exc}"
        return ProcessResult(task.image_path, task.output_path, success=False, error=msg)

    try:
        ensure_parent_dir(task.output_path)
        with task.output_path.open("w", encoding="utf-8") as f:
            json.dump(response_dict, f, ensure_ascii=False, indent=2)
        logger.debug("Successfully wrote JSON output: %s", task.output_path)
        return ProcessResult(task.image_path, task.output_path, success=True)
    except OSError as exc:
        msg = f"Failed to write JSON output: {exc}"
        logger.error("%s for %s", msg, task.output_path)
        return ProcessResult(task.image_path, task.output_path, success=False, error=msg)


def run_sequential(
        client: vision.ImageAnnotatorClient,
        tasks: Sequence[ImageTask],
        max_results: int,
        project_id: Optional[str],
        logger: logging.Logger,
) -> List[ProcessResult]:
    """Process all tasks sequentially."""
    results: List[ProcessResult] = []
    total = len(tasks)
    for idx, task in enumerate(tasks, start=1):
        result = process_single_image(client, task, max_results, project_id, logger)
        results.append(result)
        if idx % 10 == 0 or idx == total:
            logger.info("Processed %d/%d images", idx, total)
    return results


def run_parallel(
        client: vision.ImageAnnotatorClient,
        tasks: Sequence[ImageTask],
        max_results: int,
        project_id: Optional[str],
        logger: logging.Logger,
        workers: int,
) -> List[ProcessResult]:
    """
    Process tasks in parallel using a ThreadPoolExecutor.

    The same Vision client is shared among threads.
    """
    results: List[ProcessResult] = []
    total = len(tasks)
    logger.info("Processing %d images with %d worker threads.", total, workers)
    with ThreadPoolExecutor(max_workers=workers) as executor:
        future_to_task = {
            executor.submit(
                process_single_image,
                client,
                task,
                max_results,
                project_id,
                logger,
            ): task
            for task in tasks
        }

        completed = 0
        for future in as_completed(future_to_task):
            task = future_to_task[future]
            try:
                result = future.result()
            except Exception as exc:  # noqa: BLE001
                logger.error("Unhandled worker error for %s: %s", task.image_path, exc)
                result = ProcessResult(
                    image_path=task.image_path,
                    output_path=task.output_path,
                    success=False,
                    error=f"Unhandled worker error: {exc}",
                )
            results.append(result)
            completed += 1
            if completed % 10 == 0 or completed == total:
                logger.info("Processed %d/%d images", completed, total)
    return results


def parse_extensions(arg: Optional[str]) -> Set[str]:
    """Parse a comma-separated list of extensions, or return the default set."""
    if not arg:
        return set(DEFAULT_EXTENSIONS)
    exts: Set[str] = set()
    for part in arg.split(","):
        part = part.strip()
        if not part:
            continue
        if not part.startswith("."):
            part = "." + part
        exts.add(part.lower())
    return exts or set(DEFAULT_EXTENSIONS)


def parse_args(argv: Optional[Sequence[str]] = None) -> argparse.Namespace:
    """Parse CLI arguments."""
    parser = argparse.ArgumentParser(
        description=(
            "Run Google Cloud Vision LABEL_DETECTION on local images recursively and "
            "store raw JSON responses in an output directory that mirrors the input "
            "directory structure."
        )
    )
    parser.add_argument(
        "--input-dir",
        action="append",
        dest="input_dirs",
        required=True,
        help="Input directory containing images. Can be specified multiple times.",
    )
    parser.add_argument(
        "--output-dir",
        required=True,
        help="Output directory under which JSON results will be written.",
    )
    parser.add_argument(
        "--env-file",
        default=DEFAULT_ENV_FILE,
        help=f"Path to .env file (default: {DEFAULT_ENV_FILE}).",
    )
    parser.add_argument(
        "--max-results",
        type=int,
        default=DEFAULT_MAX_RESULTS,
        help=f"Maximum number of labels per image (default: {DEFAULT_MAX_RESULTS}).",
    )
    parser.add_argument(
        "--extensions",
        help=(
            "Comma-separated list of allowed image file extensions "
            "(e.g. '.jpg,.png,.tiff'). Default: .jpg,.jpeg,.png,.gif,.bmp,.tiff"
        ),
    )
    parser.add_argument(
        "--test",
        type=int,
        default=None,
        help="Test mode: only process the first N images after filtering.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help=(
            "Perform discovery and planning only; do not call Vision API and do not "
            "write output files."
        ),
    )
    parser.add_argument(
        "--workers",
        type=int,
        default=1,
        help="Number of worker threads to use (default: 1, meaning sequential).",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Reprocess all images, ignoring any existing JSON outputs.",
    )
    parser.add_argument(
        "--log-level",
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        help="Logging verbosity level (default: INFO).",
    )
    args = parser.parse_args(argv)

    if args.max_results <= 0:
        parser.error("--max-results must be a positive integer.")
    if args.test is not None and args.test <= 0:
        parser.error("--test must be a positive integer when provided.")
    if args.workers <= 0:
        parser.error("--workers must be a positive integer.")

    return args


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = parse_args(argv)

    logging.basicConfig(
        level=getattr(logging, args.log_level.upper()),
        format="[%(levelname)s] %(message)s",
    )
    logger = logging.getLogger("detect_labels")

    input_dirs = [Path(p) for p in args.input_dirs]
    output_root = Path(args.output_dir)
    env_path = Path(args.env_file)
    extensions = parse_extensions(args.extensions)

    logger.info("Using %d input directory(ies).", len(input_dirs))
    logger.debug("Input directories: %s", ", ".join(str(p) for p in input_dirs))
    logger.debug("Output directory: %s", output_root)
    logger.debug("Allowed extensions: %s", ", ".join(sorted(extensions)))

    load_env(env_path, logger)
    project_id = validate_credentials(logger)
    if project_id is None and "GOOGLE_APPLICATION_CREDENTIALS" not in os.environ:
        # validate_credentials already logged an error; double-check env in case of edge cases.
        return 1
    if "GOOGLE_APPLICATION_CREDENTIALS" not in os.environ:
        # validate_credentials only logged but returned project_id; still must enforce creds presence.
        logger.error("GOOGLE_APPLICATION_CREDENTIALS is missing after .env loading.")
        return 1

    # Discover images.
    images = find_images(input_dirs, extensions, logger)

    # Build tasks and skip existing outputs unless --force.
    tasks, skipped_existing = build_tasks(images, input_dirs, output_root, args.force, logger)

    # Apply test limit if requested.
    tasks = apply_test_limit(tasks, args.test, logger)

    if args.dry_run:
        logger.info("Dry-run mode enabled; no Vision API calls or file writes will occur.")
        for task in tasks:
            logger.info("DRY-RUN: would process %s -> %s", task.image_path, task.output_path)
        logger.info(
            "Dry-run summary: %d candidate images, %d skipped (existing), %d planned for processing.",
            len(images),
            skipped_existing,
            len(tasks),
        )
        return 0

    # Ensure output root exists before processing.
    output_root.mkdir(parents=True, exist_ok=True)

    # Initialize Vision client.
    try:
        client = init_vision_client(project_id, logger)
    except Exception:
        # Error already logged.
        return 1

    # Process tasks.
    if not tasks:
        logger.info("No images to process after filtering; exiting.")
        return 0

    if args.workers == 1:
        results = run_sequential(client, tasks, args.max_results, project_id, logger)
    else:
        results = run_parallel(client, tasks, args.max_results, project_id, logger, workers=args.workers)

    # Summarize results.
    success_count = sum(1 for r in results if r.success)
    failure_count = sum(1 for r in results if not r.success)
    logger.info(
        "Processing complete. Success: %d, Failed: %d, Skipped (existing): %d, Total discovered: %d",
        success_count,
        failure_count,
        skipped_existing,
        len(images),
    )

    # Exit code: 0 even if some images failed, as long as setup was OK.
    # Adjust to non-zero if you want failures to signal an error.
    return 0


if __name__ == "__main__":
    sys.exit(main())