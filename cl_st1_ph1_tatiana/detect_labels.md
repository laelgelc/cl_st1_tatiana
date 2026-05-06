# Master Specification: `detect_labels.py`

## 1. Overall Goal

Implement a **command-line Python tool** named `detect_labels.py` that:

1. Recursively scans one or more **local directories** for image files.
2. For each image, calls **Google Cloud Vision API** with `LABEL_DETECTION`.
3. Writes the **raw JSON response** for each image to disk:
   - One JSON file per image.
   - JSON file is named after the image (same base name, `.json` extension).
   - Output directory structure mirrors the input directory structure.
4. Supports:
   - **Incremental processing** (skip already-processed images).
   - **Parallel workers**.
   - **Test mode** to process only the first N images.
   - **Dry-run mode**.
   - Logging via Python’s `logging` module.
5. Uses an `.env` file at `env/.env` for **Google Cloud configuration**, primarily `GOOGLE_APPLICATION_CREDENTIALS`, with `GOOGLE_CLOUD_PROJECT` optional.

No label post-processing or aggregation into CSV/text is required; the output is the raw Vision JSON per image.

---

## 2. Environment & Assumptions

- Language: **Python 3.x**.
- Authentication:
  - Uses **Application Default Credentials (ADC)** via `GOOGLE_APPLICATION_CREDENTIALS`.
  - Optional project hint via `GOOGLE_CLOUD_PROJECT`.
- Project context:
  - A Google Cloud project (e.g. `cl-st1-tatiana`) exists and has **Cloud Vision API enabled**.
  - A **service account JSON key** for this project is available in the repo (e.g. under `env/`).

---

## 3. Module-Level Docstring Requirements

`detect_labels.py` **must** start with a module-level docstring that:

1. **Explains what the program does**:
   - CLI tool for Vision `LABEL_DETECTION` on local images.
   - Writes one JSON per image under an output directory, mirroring input structure.
   - Supports skipping existing outputs (`--force` toggles this), parallel workers, test mode, and dry-run.

2. **Describes authentication and configuration**:
   - Emphasize that the primary requirement is a valid **service account key** referenced by `GOOGLE_APPLICATION_CREDENTIALS`.
   - Explain that:
     - `GOOGLE_APPLICATION_CREDENTIALS` must point to the JSON key file.
     - `GOOGLE_CLOUD_PROJECT` is **optional**: if set, it provides an explicit project ID; if not, the client uses the project in the service account.
   - Mention that the script expects to load a `.env` file by default from `env/.env`, for example:

     ```text
     GOOGLE_APPLICATION_CREDENTIALS=/full/path/to/env/cl-st1-tatiana-92dcc00bf399.json
     GOOGLE_CLOUD_PROJECT=cl-st1-tatiana
     ```

3. **Provides concrete usage examples**, including:

   - Basic run:

     ```bash
     python detect_labels.py \
         --input-dir images \
         --output-dir vision_output
     ```

   - Multiple input directories:

     ```bash
     python detect_labels.py \
         --input-dir images \
         --input-dir more_images \
         --output-dir vision_output
     ```

   - Test mode (first N images):

     ```bash
     python detect_labels.py \
         --input-dir images \
         --output-dir vision_output \
         --test 20
     ```

   - Dry run:

     ```bash
     python detect_labels.py \
         --input-dir images \
         --output-dir vision_output \
         --dry-run
     ```

   - With workers:

     ```bash
     python detect_labels.py \
         --input-dir images \
         --output-dir vision_output \
         --workers 4
     ```

   - Force reprocessing:

     ```bash
     python detect_labels.py \
         --input-dir images \
         --output-dir vision_output \
         --force
     ```

4. **Documents all command-line arguments** (see section 4).

5. **Summarizes the processing steps** (e.g. 1–7 list as in section 11).

6. **Explains logging behavior**:
   - Uses `logging`.
   - `--log-level` controls verbosity.

---

## 4. Command-Line Interface

Use `argparse` (or similar) to implement the following CLI.

### 4.1 Required Arguments

- `--input-dir DIR` (required, **repeatable**):
  - One or more directories containing images.
  - Recursively scanned.
  - Can be used multiple times:
    - `--input-dir images --input-dir more_images`.

- `--output-dir DIR` (required):
  - Root directory where JSON output files are stored.
  - Script must create this directory and needed subdirectories.

### 4.2 Optional Arguments

- `--env-file PATH` (default: `env/.env`):
  - Path to the `.env` file.
  - In this project, the default should be `env/.env`.

- `--max-results N` (default: reasonable value, e.g. `50` or `150`):
  - Maximum number of labels requested per image.

- `--extensions EXT1,EXT2,...`:
  - Comma-separated list of allowed image file extensions, case-insensitive.
  - Default set: `.jpg,.jpeg,.png,.gif,.bmp,.tiff`.

- `--test N`:
  - Test mode: after discovery and skipping existing outputs (if not `--force`), sort remaining images and process **only the first N**.
  - N must be a positive integer.

- `--dry-run` (flag):
  - Perform all discovery and planning but **do not** call Vision and do **not** write JSON files.
  - Log what would be processed and where outputs would go.

- `--workers N` (default: `1`):
  - Number of workers used for parallel processing.
  - `1` means sequential; `N > 1` uses a worker pool.

- `--force` (flag):
  - Ignore existing JSON output files and reprocess all images.
  - Without `--force`, the script skips images that already have output JSON.

- `--log-level LEVEL` (default: `INFO`):
  - One of `DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL`.

---

## 5. Configuration & Authentication

### 5.1 `.env` Loading (Default: `env/.env`)

- On startup, before creating the Vision client:

  1. Determine `.env` path:
     - Use `--env-file` if provided.
     - Otherwise, default to `env/.env` (relative to the working directory or script root; clarify and implement consistently).
  2. If the `.env` file exists:
     - Parse lines of form `KEY=VALUE` (ignore blank lines and `#` comments).
     - For each pair:
       - Set `os.environ[KEY] = VALUE`.
  3. If it does not exist:
     - Log a `WARNING` but allow environment variables to be set externally.

- Keys of interest:

  - **Required:**
    - `GOOGLE_APPLICATION_CREDENTIALS`  
      Must point to a service account JSON key that has permission to call Vision in the intended project.

  - **Optional:**
    - `GOOGLE_CLOUD_PROJECT`  
      If set, the script should pass/use this as the explicit project ID. If not set, the Vision client relies on the project encoded in the service account.

- Validation:

  - If `GOOGLE_APPLICATION_CREDENTIALS` is not present in `os.environ` after `.env` loading:
    - Log an `ERROR` indicating that credentials are required (and how to set them).
    - Exit with non-zero status.
  - `GOOGLE_CLOUD_PROJECT` is **not strictly required**:
    - If present, use it.
    - If absent, proceed and let the client infer the project.

### 5.2 Vision Client Initialization

- Initialize the Vision client using Application Default Credentials.
- If `GOOGLE_CLOUD_PROJECT` is present, configure the client to use that project explicitly where applicable.
- If client initialization fails:
  - Log `ERROR` and exit with non-zero status.

---

## 6. Image Discovery

For each `--input-dir`:

1. Recursively traverse all subdirectories.
2. For each file:
   - Check its extension against the allowed set (case-insensitive).
   - If it matches, include as a candidate image.
3. Collect all candidate image paths in a list.

After all input dirs:

- Log at `INFO` the total number of candidate images discovered.

---

## 7. Output Path Computation

For each candidate image:

1. Determine the root `--input-dir` it belongs to.
2. Compute its **relative path** under that root.
   - Example:
     - Input dir: `images`
     - Image: `images/sub/dir/image01.jpg`
     - Relative path: `sub/dir/image01.jpg`
3. Under `--output-dir`, create a parallel path with `.json` extension:
   - `output_dir/sub/dir/image01.json`.
4. This output path is used as the location for the Vision JSON.

The same approach applies if there are multiple input dirs: each image’s relative path is computed relative to its own root.

---

## 8. Skipping Already-Processed Files (`--force`)

1. For each candidate image, compute its output JSON path (as above).
2. If `--force` is **not** set:
   - If the output JSON exists:
     - Skip this image (do not include in processing list).
     - Optionally log at `DEBUG` that it was skipped because output exists.
3. If `--force` is set:
   - Include all images, ignoring existing outputs.

After filtering:

- Log at `INFO` the number of images remaining to be processed.

---

## 9. Test Mode (`--test N`)

If `--test N` is provided:

1. Take the filtered list of `(image_path, output_path)` pairs.
2. Sort them in a deterministic way (e.g. by `str(image_path)`).
3. Keep only the first **N**.
4. Log at `INFO` that test mode is active and how many images will be processed.

If `N >=` number of remaining images, process all remaining images.

---

## 10. Dry-Run Mode (`--dry-run`)

If `--dry-run` is set:

1. Load `.env` and configure logging as usual.
2. Discover images, compute output paths, apply skip-existing and test-mode filters.
3. For each image that would be processed:
   - Log (at `INFO` or `DEBUG`):
     - Input image path.
     - Planned JSON output path.
4. Exit **without**:
   - Reading image files.
   - Initializing or using the Vision client (this can be skipped).
   - Writing any JSON files.

---

## 11. Vision API Calls & JSON Writing

For each image in the final processing list (no dry-run):

1. **Read the image bytes**:
   - Open file in binary mode.
   - If unreadable:
     - Log `WARNING` with the path and exception.
     - Mark as failed and continue to next image.

2. **Call Vision `LABEL_DETECTION`**:
   - Use the Vision client configured from ADC.
   - Request:
     - `LABEL_DETECTION` with `maxResults = --max-results`.
   - Implement simple retry for transient errors (HTTP 429, 500, etc.):
     - Up to e.g. 3 attempts with exponential backoff.
     - On final failure:
       - Log `ERROR` with the image path and error.
       - Mark as failed, skip JSON write.

3. **Serialize response to JSON**:
   - Convert the Vision response to a Python dict (e.g. `.to_dict()` or equivalent).
   - This dict should reflect the standard Vision `images:annotate` response structure without extra transformations.

4. **Write output JSON**:
   - Ensure parent directories for the output path exist.
   - `json.dump` the dict to the output file (UTF-8).
   - Handle write errors:
     - Log `ERROR` and mark as failed.

---

## 12. Parallel Processing (`--workers`)

If `--workers > 1`:

- Use a worker pool to process images in parallel.

Suggested implementation:

- Use `concurrent.futures.ThreadPoolExecutor` (simpler for I/O-bound Vision calls with a shared client) **or** `ProcessPoolExecutor` (each process creates its own client).
- Each worker:
  - Accepts `(image_path, output_path)` plus configuration (`max_results`, etc.).
  - Performs: read image → call Vision → write JSON.
  - Returns a small result object:
    - At least: `image_path`, `success` (bool), and `error` (optional message).

The main process:

1. Submits all tasks to the executor.
2. Tracks completed tasks and progress.
3. Logs progress periodically at `INFO`:
   - e.g. `"Processed 100/532 images"`.
4. Aggregates results and logs a final summary:
   - Total processed.
   - Total skipped (existing outputs).
   - Total failed.

If `--workers` is absent or `1`, run sequentially in the main thread.

---

## 13. Logging Requirements

Use Python’s `logging` module.

### 13.1 Setup

- In `main()`:
  - Configure logging to stderr.
  - Level from `--log-level` (default `INFO`).
  - Suggested format:

    ```text
    [%(levelname)s] %(message)s
    ```

### 13.2 Expected Logging Behavior

- `INFO`:
  - Number of input directories.
  - Number of candidate images found.
  - Number remaining after skipping existing outputs.
  - Whether test mode is enabled (and N).
  - Whether dry-run is enabled.
  - Periodic progress updates.
  - Final summary (success/skip/fail counts).

- `DEBUG`:
  - Detailed actions (e.g. “Skipping because JSON exists: …”).
  - Per-image diagnostics, if needed.

- `WARNING`:
  - Non-fatal issues (e.g. unreadable files).

- `ERROR`:
  - Fatal setup problems (e.g. missing `GOOGLE_APPLICATION_CREDENTIALS`).
  - Vision API failures for specific images after retries.
  - JSON write failures.

On fatal configuration errors, exit with a non-zero status code.

---

## 14. Suggested Internal Structure (Non-binding)

A clear, modular structure is recommended, e.g.:

- `main()`
  - Parse arguments.
  - Configure logging.
  - Load `.env` from `--env-file` or `env/.env`.
  - Validate presence of `GOOGLE_APPLICATION_CREDENTIALS`.
  - Optionally log `GOOGLE_CLOUD_PROJECT` if present.
  - If not `--dry-run`, initialize Vision client.
  - Discover candidate images (`find_images`).
  - For each, compute output path.
  - Apply skip-existing (unless `--force`).
  - Apply `--test` limitation.
  - If `--dry-run`, log planned work and exit.
  - Else, process images (sequential or via worker pool).
  - Log summary and exit.

- Example helper functions:

  - `load_env(env_path: str) -> None`
  - `find_images(input_dirs: list[str], extensions: set[str]) -> list[Path]`
  - `compute_output_path(image_path: Path, input_dirs: list[Path], output_dir: Path) -> Path`
  - `filter_already_processed(...) -> list[(image_path, output_path)]`
  - `limit_images_for_test(...) -> list[(image_path, output_path)]`
  - `process_image(...) -> (success: bool, error_message: Optional[str])`
  - `run_sequential(...)` / `run_parallel(...)`

The exact structure is up to the implementer as long as behavior matches this spec.
