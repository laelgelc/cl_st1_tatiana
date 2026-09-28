# Master Specification: `detect_labels.py`

## 1. Overall Goal

Implement a **command-line Python tool** named `detect_labels.py` that:

1. Recursively scans one or more **local directories** for image files.
2. For each image, calls **Google Cloud Vision API** with `LABEL_DETECTION`.
3. Writes the **raw JSON response** for each image to disk:
   - One JSON file per image.
   - JSON file is named after the image, with the same base name and a `.json` extension.
   - Output directory structure mirrors the input directory structure.
4. Supports:
   - **Incremental processing** by skipping already processed images by default.
   - **Forced reprocessing** with `--force`.
   - **Retrying empty or failed label outputs** from a TSV list via `--retry-empty-tsv`.
   - **Retrying specific files** via repeatable `--retry-file`.
   - **Parallel workers**.
   - **Test mode** to process only the first N selected images.
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
- Google Cloud context:
  - A Google Cloud project exists and has **Cloud Vision API enabled**.
  - A **service account JSON key** for this project is available.
  - The service account has permission to call the Vision API.
- Input data:
  - Input images are local files under one or more input directories.
  - File types are selected by extension.
- Retry data:
  - Retry list files are TSV files with a `filepath` column.
  - The `filepath` values normally point to output JSON files that should be regenerated.

---

## 3. Module-Level Docstring Requirements

`detect_labels.py` **must** start with a module-level docstring that:

1. **Explains what the program does**:
   - CLI tool for Vision `LABEL_DETECTION` on local images.
   - Writes one JSON per image under an output directory, mirroring input structure.
   - Supports skipping existing outputs, forced reprocessing, retry modes, parallel workers, test mode, and dry-run.

2. **Describes authentication and configuration**:
   - Emphasize that the primary requirement is a valid **service account key** referenced by `GOOGLE_APPLICATION_CREDENTIALS`.
   - Explain that:
     - `GOOGLE_APPLICATION_CREDENTIALS` must point to the JSON key file.
     - `GOOGLE_CLOUD_PROJECT` is **optional**: if set, it provides an explicit project ID; if not, the client uses the project in the service account.
   - Mention that the script expects to load a `.env` file by default from `env/.env`, for example:

```plain text
GOOGLE_APPLICATION_CREDENTIALS=/full/path/to/env/service-account-key.json
     GOOGLE_CLOUD_PROJECT=your-google-cloud-project
```


3. **Provides concrete usage examples**, including:

   - Basic run:

```shell script
python detect_labels.py \
         --input-dir images \
         --output-dir vision_output
```


   - Multiple input directories:

```shell script
python detect_labels.py \
         --input-dir images \
         --input-dir more_images \
         --output-dir vision_output
```


   - Test mode:

```shell script
python detect_labels.py \
         --input-dir images \
         --output-dir vision_output \
         --test 20
```


   - Dry run:

```shell script
python detect_labels.py \
         --input-dir images \
         --output-dir vision_output \
         --dry-run
```


   - With workers:

```shell script
python detect_labels.py \
         --input-dir images \
         --output-dir vision_output \
         --workers 4
```


   - Force reprocessing:

```shell script
python detect_labels.py \
         --input-dir images \
         --output-dir vision_output \
         --force
```


   - Retry all files listed in a TSV:

```shell script
python detect_labels.py \
         --input-dir corpus/deduplicated_2 \
         --output-dir corpus/02_labelled \
         --retry-empty-tsv corpus/label_empty.tsv \
         --workers 4
```


   - Retry selected files from a TSV:

```shell script
python detect_labels.py \
         --input-dir corpus/deduplicated_2 \
         --output-dir corpus/02_labelled \
         --retry-empty-tsv corpus/label_empty.tsv \
         --retry-file saude202003_n_00026_00000004 \
         --retry-file saude202003_n_00027_00000004 \
         --workers 4
```


   - Retry specific output JSON paths directly:

```shell script
python detect_labels.py \
         --input-dir corpus/deduplicated_2 \
         --output-dir corpus/02_labelled \
         --retry-file corpus/02_labelled/saude202003_n_00026_00000004.json \
         --retry-file corpus/02_labelled/saude202003_n_00027_00000004.json \
         --workers 4
```


4. **Documents all command-line arguments**.

5. **Summarizes the processing steps**.

6. **Explains logging behavior**:
   - Uses `logging`.
   - `--log-level` controls verbosity.

---

## 4. Command-Line Interface

Use `argparse` or equivalent to implement the following CLI.

### 4.1 Required Arguments

- `--input-dir DIR` (required, **repeatable**):
  - One or more directories containing images.
  - Recursively scanned.
  - Can be used multiple times:
    - `--input-dir images --input-dir more_images`.
  - Required even in retry mode, because retry output JSON paths must be mapped back to source image files.

- `--output-dir DIR` (required):
  - Root directory where JSON output files are stored.
  - Script must create this directory and needed subdirectories.
  - In normal mode, output paths are computed under this directory.
  - In retry mode, this directory is used to interpret listed JSON output paths and map them back to source images.

### 4.2 Optional Arguments

- `--env-file PATH` (default: `env/.env`):
  - Path to the `.env` file.
  - In this project, the default should be `env/.env`.

- `--max-results N` (default: `50`):
  - Maximum number of labels requested per image.
  - Must be a positive integer.

- `--extensions EXT1,EXT2,...`:
  - Comma-separated list of allowed image file extensions, case-insensitive.
  - If an extension is supplied without a leading dot, add one internally.
  - Default set:
    - `.jpg`
    - `.jpeg`
    - `.png`
    - `.gif`
    - `.bmp`
    - `.tiff`

- `--test N`:
  - Test mode.
  - After task construction, sort selected tasks deterministically by image path and process **only the first N**.
  - Applies to both normal processing and retry modes.
  - N must be a positive integer.
  - If `N >=` number of selected tasks, process all selected tasks.

- `--dry-run` (flag):
  - Perform discovery and planning but **do not**:
    - Call Vision.
    - Read image bytes.
    - Write JSON files.
    - Initialize the Vision client.
  - Log what would be processed and where outputs would go.
  - Applies to both normal processing and retry modes.

- `--workers N` (default: `1`):
  - Number of worker threads used for processing.
  - `1` means sequential processing.
  - `N > 1` uses a worker pool.
  - Must be a positive integer.

- `--force` (flag):
  - Normal mode:
    - Ignore existing JSON output files and reprocess all images.
  - Without `--force`, normal mode skips images that already have output JSON.
  - Retry mode:
    - Existing JSON outputs are overwritten regardless of `--force`.
    - Therefore, in retry mode, `--force` is effectively implied.

- `--retry-empty-tsv PATH`:
  - TSV file containing a `filepath` column of output JSON files to retry.
  - Example:

```plain text
filepath
    corpus/02_labelled/image01.json
    corpus/02_labelled/image02.json
```


  - The script reads all non-empty values in the `filepath` column.
  - Each listed output JSON path is mapped back to its corresponding source image.
  - Existing JSON outputs are not skipped.

- `--retry-file VALUE` (repeatable):
  - Retry a specific file.
  - Can be used in two ways:
    1. **With `--retry-empty-tsv`**:
       - Filters the TSV retry list to matching files only.
    2. **Without `--retry-empty-tsv`**:
       - The supplied values themselves are treated as retry output JSON paths or stems.
  - Accepts:
    - Full output JSON path, e.g. `corpus/02_labelled/image01.json`.
    - Relative output JSON path.
    - Filename, e.g. `image01.json`.
    - Stem, e.g. `image01`.
  - Can be repeated:
    - `--retry-file image01 --retry-file image02`.

- `--log-level LEVEL` (default: `INFO`):
  - One of:
    - `DEBUG`
    - `INFO`
    - `WARNING`
    - `ERROR`
    - `CRITICAL`

---

## 5. Configuration & Authentication

### 5.1 `.env` Loading (Default: `env/.env`)

On startup, before creating the Vision client:

1. Determine `.env` path:
   - Use `--env-file` if provided.
   - Otherwise, default to `env/.env`.

2. If the `.env` file exists:
   - Parse lines of form `KEY=VALUE`.
   - Ignore:
     - Blank lines.
     - Lines beginning with `#`.
     - Invalid lines without `=`.
   - For each parsed pair:
     - Strip surrounding whitespace from key and value.
     - Set `os.environ[KEY] = VALUE`.

3. If the `.env` file does not exist:
   - Log a `WARNING`.
   - Allow environment variables to be set externally.

Keys of interest:

- **Required:**
  - `GOOGLE_APPLICATION_CREDENTIALS`
    - Must point to a service account JSON key that has permission to call Vision in the intended project.

- **Optional:**
  - `GOOGLE_CLOUD_PROJECT`
    - If set, the script should use this as the explicit project ID when applicable.
    - If not set, the Vision client relies on the project encoded in the service account.

Validation:

- If `GOOGLE_APPLICATION_CREDENTIALS` is not present in `os.environ` after `.env` loading:
  - Log an `ERROR` indicating that credentials are required and how to set them.
  - Exit with non-zero status.
- `GOOGLE_CLOUD_PROJECT` is **not strictly required**:
  - If present, log and use it.
  - If absent, proceed and let the client infer the project.

### 5.2 Vision Client Initialization

- Initialize the Vision client using Application Default Credentials.
- If `GOOGLE_CLOUD_PROJECT` is present, configure or pass the project ID where supported.
- If client initialization fails:
  - Log `ERROR`.
  - Exit with non-zero status.
- In `--dry-run` mode:
  - Do **not** initialize the Vision client.

---

## 6. Image Discovery

Normal mode image discovery applies when neither `--retry-empty-tsv` nor `--retry-file` is used.

For each `--input-dir`:

1. Check that the path exists.
   - If it does not exist, log `WARNING` and skip it.
2. Check that the path is a directory.
   - If it is not a directory, log `WARNING` and skip it.
3. Recursively traverse all subdirectories.
4. For each file:
   - Check its extension against the allowed set.
   - Matching should be case-insensitive.
   - If it matches, include the file as a candidate image.
5. Store image paths as resolved `Path` objects where practical.

After all input directories:

- Log at `INFO` the total number of candidate images discovered.

---

## 7. Output Path Computation

For each candidate image in normal mode:

1. Determine the root `--input-dir` it belongs to.
2. Compute its **relative path** under that input root.
   - Example:
     - Input dir: `images`
     - Image: `images/sub/dir/image01.jpg`
     - Relative path: `sub/dir/image01.jpg`
3. Under `--output-dir`, create a parallel path with `.json` extension:
   - `output_dir/sub/dir/image01.json`
4. This output path is used as the location for the Vision JSON.

The same approach applies if there are multiple input dirs: each image’s relative path is computed relative to its own root.

If no input root matches a candidate image path, fall back to placing a JSON file named after the image basename directly under `--output-dir`.

---

## 8. Skipping Already-Processed Files (`--force`)

Normal mode:

1. For each candidate image, compute its output JSON path.
2. If `--force` is **not** set:
   - If the output JSON exists:
     - Skip this image.
     - Do not include it in the processing task list.
     - Optionally log at `DEBUG` that it was skipped because output exists.
3. If `--force` is set:
   - Include all candidate images, ignoring existing outputs.

After filtering:

- Log at `INFO`:
  - Number of images remaining to process.
  - Number skipped because outputs already existed.

Retry modes:

- Do **not** apply skip-existing filtering.
- Existing JSON outputs are overwritten.
- `--force` is effectively implied, whether or not the user supplies it.

---

## 9. Retry Modes

Retry mode is used to regenerate JSON outputs that were empty, failed, incomplete, or otherwise need to be rerun.

There are two retry entry points:

1. `--retry-empty-tsv PATH`
2. `--retry-file VALUE`

These can be used separately or together.

### 9.1 Retry List Mode: `--retry-empty-tsv`

`--retry-empty-tsv` points to a TSV file containing a `filepath` column.

Example:

```plain text
filepath
corpus/02_labelled/saude202003_n_00026_00000004.json
corpus/02_labelled/saude202003_n_00027_00000004.json
```


Required behaviour:

1. Validate that the TSV file exists and is a file.
2. Read it with tab delimiters.
3. Verify that it contains a column named `filepath`.
4. For each row:
   - Read the `filepath` value.
   - Strip whitespace.
   - Ignore empty values.
   - Interpret the value as an output JSON path to retry.
5. Log the number of retry output paths loaded.
6. Convert each output JSON path to an `ImageTask` by finding the corresponding source image.
7. Do not skip existing output JSON files.

### 9.2 Specific Retry Mode: `--retry-file`

`--retry-file` can be repeated.

Example:

```shell script
python detect_labels.py \
    --input-dir corpus/deduplicated_2 \
    --output-dir corpus/02_labelled \
    --retry-file corpus/02_labelled/saude202003_n_00026_00000004.json \
    --retry-file saude202003_n_00027_00000004
```


Required behaviour:

- If used **with** `--retry-empty-tsv`:
  - Treat `--retry-file` values as filters on the TSV list.
  - Only TSV paths matching one of the filters are retried.

- If used **without** `--retry-empty-tsv`:
  - Treat each `--retry-file` value as a retry output path or stem.
  - Build retry tasks from these values directly.

A `--retry-file` value should match if it equals any of the following for a retry output path:

- Full path string.
- POSIX path string.
- Filename, e.g. `image01.json`.
- Stem, e.g. `image01`.

### 9.3 Mapping Retry Output JSON Paths Back to Source Images

Given an output JSON path, the script must locate the original image under one of the `--input-dir` roots.

Required mapping algorithm:

1. Interpret the retry value as an output JSON path.
2. Try to compute its relative path under `--output-dir`.
   - Example:
     - `--output-dir`: `corpus/02_labelled`
     - Retry path: `corpus/02_labelled/sub/image01.json`
     - Relative path: `sub/image01.json`
3. Remove the `.json` suffix from the relative path.
4. For each input directory:
   - For each allowed image extension:
     - Construct a candidate path:
       - `input_dir / relative_without_suffix.with_suffix(extension)`
     - If it exists and is a file, use it.
5. If direct relative matching fails:
   - Search recursively under each input directory for a file with the same stem and one of the allowed image extensions.
   - Use the first deterministic match, e.g. sorted by path.
6. If no matching source image is found:
   - Log a `WARNING`.
   - Skip that retry output path.

Example mapping:

```plain text
Output JSON:
corpus/02_labelled/saude202003_n_00026_00000004.json

Possible source image:
corpus/deduplicated_2/saude202003_n_00026_00000004.jpg
```


### 9.4 Retry Task Deduplication

When building retry tasks:

- Deduplicate tasks by `(resolved image_path, resolved output_path)`.
- If the same output appears multiple times, process it only once.
- Log the number of retry tasks built.

### 9.5 Retry Mode and `--test`

If `--test N` is supplied in retry mode:

1. Build the retry task list first.
2. Sort tasks by image path.
3. Keep only the first N.
4. Log that test mode is active.

### 9.6 Retry Mode and `--dry-run`

If `--dry-run` is supplied in retry mode:

- Build retry tasks.
- Log each planned source image and output JSON mapping.
- Do not initialize Vision.
- Do not call Vision.
- Do not write files.

---

## 10. Test Mode (`--test N`)

If `--test N` is provided:

1. Take the final task list:
   - Normal mode: after discovery and skip-existing filtering.
   - Retry mode: after retry task construction.
2. Sort tasks deterministically by `str(image_path)`.
3. Keep only the first **N**.
4. Log at `INFO` that test mode is active and how many images will be processed.

If `N >=` the number of selected tasks, process all selected tasks.

---

## 11. Dry-Run Mode (`--dry-run`)

If `--dry-run` is set:

1. Load `.env` and configure logging as usual.
2. Validate credentials environment variables as usual.
3. Build the task list:
   - Normal mode:
     - Discover images.
     - Compute output paths.
     - Apply skip-existing filtering.
   - Retry mode:
     - Load retry paths or retry-file values.
     - Map output JSON paths back to source images.
     - Build retry tasks.
4. Apply `--test`, if provided.
5. For each task that would be processed, log:
   - Input image path.
   - Planned JSON output path.
6. Log a dry-run summary:
   - Candidate or selected images.
   - Skipped existing outputs.
   - Planned processing count.
7. Exit **without**:
   - Reading image files.
   - Initializing or using the Vision client.
   - Calling the Vision API.
   - Writing JSON files.

---

## 12. Vision API Calls & JSON Writing

For each image in the final processing list when not in dry-run mode:

1. **Read the image bytes**:
   - Open file in binary mode.
   - If unreadable:
     - Log `WARNING` with the path and exception.
     - Mark as failed and continue to the next image.

2. **Call Vision `LABEL_DETECTION`**:
   - Use the Vision client configured from ADC.
   - Request:
     - `LABEL_DETECTION`.
     - `maxResults = --max-results`.
   - Implement retry for transient errors:
     - Up to 3 attempts.
     - Exponential backoff, e.g. 1 second, 2 seconds, 4 seconds.
   - Treat the following as transient:
     - Deadline exceeded.
     - Service unavailable.
     - Internal server error.
     - Too many requests.
     - HTTP-like status codes `429`, `500`, `502`, `503`, `504`, where available.
   - On final failure:
     - Log `ERROR` with the image path and error.
     - Mark as failed.
     - Skip JSON write.

3. **Serialize response to JSON**:
   - Convert the Vision response to a Python dictionary.
   - Prefer `.to_dict()` if available.
   - Otherwise use an equivalent protobuf-to-dictionary conversion.
   - The result should reflect the standard Vision `images:annotate` response structure without label post-processing.

4. **Write output JSON**:
   - Ensure parent directories for the output path exist.
   - Write JSON as UTF-8.
   - Use `ensure_ascii=False`.
   - Use indentation for readability, e.g. `indent=2`.
   - Handle write errors:
     - Log `ERROR`.
     - Mark as failed.

---

## 13. Parallel Processing (`--workers`)

If `--workers > 1`:

- Use a worker pool to process images in parallel.

Recommended implementation:

- Use `concurrent.futures.ThreadPoolExecutor`, because the work is mostly I/O-bound and involves network API calls.
- A shared Vision client may be used across worker threads if supported by the client library.
- Alternatively, a separate client per worker may be used if needed.

Each worker should:

1. Accept an image task and processing configuration.
2. Read image bytes.
3. Call Vision with retry logic.
4. Write JSON output.
5. Return a result object containing:
   - `image_path`
   - `output_path`
   - `success`
   - Optional `error`

The main process should:

1. Submit all tasks to the executor.
2. Track completed tasks and progress.
3. Log progress periodically at `INFO`, for example:
   - `Processed 100/532 images`
4. Aggregate results and log a final summary:
   - Success count.
   - Failure count.
   - Skipped existing count.
   - Total discovered or selected count.

If `--workers` is absent or `1`, run sequentially in the main thread.

---

## 14. Logging Requirements

Use Python’s `logging` module.

### 14.1 Setup

In `main()`:

- Configure logging to stderr.
- Set level from `--log-level` (default `INFO`).
- Suggested format:

```plain text
[%(levelname)s] %(message)s
```


### 14.2 Expected Logging Behavior

- `INFO`:
  - Number of input directories.
  - Input/output configuration summary.
  - Number of candidate images found in normal mode.
  - Number remaining after skipping existing outputs.
  - Number skipped because output existed.
  - Whether retry mode is enabled.
  - Number of retry paths loaded.
  - Number of retry tasks built.
  - Whether test mode is enabled and how many tasks are selected.
  - Whether dry-run is enabled.
  - Periodic progress updates.
  - Final summary.

- `DEBUG`:
  - Detailed actions, such as:
    - Scanning directories.
    - Discovered image paths.
    - Computed output paths.
    - Skipping because JSON exists.
    - Vision client initialization success.
    - Per-image processing start and output write success.

- `WARNING`:
  - Non-fatal issues, such as:
    - Input directory does not exist.
    - Input path is not a directory.
    - `.env` file does not exist.
    - Source image for a retry output could not be found.
    - Image file could not be read.
    - Transient Vision errors before retry.

- `ERROR`:
  - Fatal setup problems, such as:
    - Missing `GOOGLE_APPLICATION_CREDENTIALS`.
    - Invalid retry TSV.
    - Vision client initialization failure.
  - Per-image unrecoverable failures:
    - Vision API failure after retries.
    - JSON write failure.

On fatal configuration errors, exit with a non-zero status code.

Per-image failures after successful setup may be reported in the final summary. The script may still exit with status code `0` unless a stricter failure policy is explicitly added.

---

## 15. Exit Codes

Recommended behaviour:

- Return `0` when:
  - Configuration is valid.
  - The script completes normal processing, retry processing, or dry-run planning.
  - Some individual images may have failed, but the overall run completed.

- Return non-zero when:
  - Required credentials are missing.
  - CLI argument validation fails.
  - Retry TSV file is missing, unreadable, or invalid.
  - Vision client initialization fails.
  - An unrecoverable setup error occurs.

---

## 16. Suggested Internal Structure (Non-binding)

A clear, modular structure is recommended.

### 16.1 Data Containers

Recommended data classes:

- `ImageTask`
  - `image_path: Path`
  - `output_path: Path`

- `ProcessResult`
  - `image_path: Path`
  - `output_path: Path`
  - `success: bool`
  - `error: Optional[str]`

### 16.2 Main Flow

`main()` should:

1. Parse arguments.
2. Configure logging.
3. Convert CLI path strings to `Path` objects.
4. Parse allowed extensions.
5. Load `.env`.
6. Validate credentials.
7. Build tasks:
   - Retry TSV mode if `--retry-empty-tsv` is set.
   - Specific retry mode if `--retry-file` is set without `--retry-empty-tsv`.
   - Normal discovery mode otherwise.
8. Apply `--test`, if provided.
9. If `--dry-run`:
   - Log planned work.
   - Exit.
10. Create output root directory.
11. Initialize Vision client.
12. If no tasks remain:
   - Log and exit.
13. Process tasks:
   - Sequentially if `--workers == 1`.
   - In parallel if `--workers > 1`.
14. Summarize results.
15. Return an appropriate exit code.

### 16.3 Suggested Helper Functions

The exact function names are flexible, but the implementation should include helpers equivalent to:

- `load_env(env_path: Path, logger: logging.Logger) -> None`
- `validate_credentials(logger: logging.Logger) -> Optional[str]`
- `init_vision_client(project_id: Optional[str], logger: logging.Logger) -> vision.ImageAnnotatorClient`
- `parse_extensions(arg: Optional[str]) -> Set[str]`
- `find_images(input_dirs: Sequence[Path], extensions: Set[str], logger: logging.Logger) -> List[Path]`
- `compute_output_path(image_path: Path, input_dirs: Sequence[Path], output_root: Path) -> Path`
- `build_tasks(...) -> Tuple[List[ImageTask], int]`
- `read_retry_output_paths_from_tsv(tsv_path: Path, logger: logging.Logger) -> List[Path]`
- `retry_file_matches(path: Path, retry_filters: Set[str]) -> bool`
- `output_path_to_image_task(...) -> Optional[ImageTask]`
- `build_retry_tasks(...) -> List[ImageTask]`
- `apply_test_limit(tasks: List[ImageTask], limit: Optional[int], logger: logging.Logger) -> List[ImageTask]`
- `is_transient_error(exc: Exception) -> bool`
- `call_vision_label_detection(...) -> dict`
- `ensure_parent_dir(path: Path) -> None`
- `process_single_image(...) -> ProcessResult`
- `run_sequential(...) -> List[ProcessResult]`
- `run_parallel(...) -> List[ProcessResult]`
- `parse_args(argv: Optional[Sequence[str]] = None) -> argparse.Namespace`
- `main(argv: Optional[Sequence[str]] = None) -> int`

The exact structure is up to the implementer as long as behaviour matches this specification.

---

## 17. Non-Goals

The script should **not**:

- Download images from URLs.
- Modify or deduplicate images.
- Perform label normalization, lemmatization, translation, filtering, or aggregation.
- Generate CSV, TSV, Excel, LaTeX, or summary label reports.
- Delete source images or output JSON files.
- Retry based on label semantics; retry is file-based only.
- Depend on notebook execution.

The script’s responsibility is limited to **image discovery/task selection → Vision label detection → raw JSON output writing**.