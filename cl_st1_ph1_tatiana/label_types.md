# Specification: `label_types.py`

## 1. Purpose

`label_types.py` converts Google Vision label annotations stored in JSON files into simple text label lists:

- Reads all `*.json` files from an input directory.
- For each file, collects the (unique) label descriptions.
- Converts each description to lowercase.
- Replaces spaces in each (lowercased) description with underscores.
- Writes one `.txt` file per input `.json` into an output directory.
- Each output `.txt` contains one label per line.

---

## 2. Command-line interface

Invocation:

```shell
python label_types.py \
    --input-dir corpus/02_labelled \
    --output-dir corpus/03_label_types
```

Arguments:

1. `--input-dir` (required)
   - Directory containing input `*.json` files.
   - Must exist and be a directory.

2. `--output-dir` (required)
   - Directory in which `.txt` files are written.
   - Created if it does not exist (including parents).

3. `--verbose` (optional flag)
   - When present, prints info/progress messages to stderr.

4. `--force` (optional flag, behavior as before)
   - When present, allows overwriting existing `.txt` files.
   - When absent, either:
     - overwrite silently, or
     - skip and warn.  
   - We can choose one; default proposal: overwrite silently to keep it simple.

---

## 3. Input processing

### 3.1 File selection

- Only files whose names end with `.json` (case-sensitive) in `--input-dir` (no recursion).
- Files processed in lexicographical order by filename.

### 3.2 JSON structure

Each file is expected to have a structure like:

```json
{
  "responses": [
    {
      "labelAnnotations": [
        { "description": "Some label", ... },
        ...
      ]
    },
    ...
  ]
}
```

Only `description` is used.

Handling:

- If `responses` is missing/empty/non-list → treat as “no labels”.
- For each `resp` in `responses`:
  - If `labelAnnotations` is missing/empty/non-list → “no labels” for that `resp`.
  - For each label in `labelAnnotations`, read `description` if it’s a string; otherwise skip.

---

## 4. Label transformation and deduplication

For each input JSON file:

1. Collect all valid `description` strings in **order of appearance**:
   - First by `responses` index,
   - then by `labelAnnotations` index.

2. **Deduplicate per file**:
   - Keep only the **first occurrence** of each description.
   - Subsequent occurrences of the same exact description string (case-sensitive) in the same file are ignored.
   - Deduplication is done before any transformation.

3. Transform each remaining description:
   - First convert the description to **lowercase**.
     - Example: `"Commercial building"` → `"commercial building"`.
   - Then replace spaces with underscores:
     - Every `" "` becomes `"_"`.
     - Example: `"commercial building"` → `"commercial_building"`.
   - No other characters are changed.

4. The order in the output `.txt`:
   - The order of first occurrence in the JSON, after deduplication and transformation.

If there are no valid descriptions after this process:

- Write an **empty** `.txt` file for that JSON (0 lines, or 0 bytes).

---

## 5. Output format

For an input `X.json`, the output is `X.txt` in `--output-dir`.

- Encoding: UTF-8.
- Content: one transformed label per line, no extra leading/trailing spaces on each line.
- A trailing newline at the end of the file is acceptable.

Example:

Given descriptions (in the JSON):

- `"Commercial building"`
- `"Headquarters"`
- `"High-rise building"`
- `"Corporate headquarters"`

The output `X.txt` is:

```text
commercial_building
headquarters
high-rise_building
corporate_headquarters
```

If `"Headquarters"` appeared twice, it would still appear only once in the `.txt`, in the position of its first occurrence (as `headquarters`).

---

## 6. Error handling

- **Invalid JSON**:
  - Log an error to stderr with the filename and parsing error.
  - Skip output for that file.
  - Program exit code: we can either:
    - non-zero if any file failed, or
    - always zero as long as at least one file succeeded.  
  - Proposal: non-zero if any file fails, so problems are visible in scripts.

- **Filesystem errors**:
  - If input directory is invalid or output directory cannot be created/written to:
    - Print a clear error to stderr and exit with non-zero status.

- **No JSON files**:
  - Warn to stderr (`No JSON files found in ...`) and exit non-zero (nothing to do).

---

## 7. Verbose logging

With `--verbose`:

- At start:

  ```text
  Found N JSON files in <input-dir>
  ```

- For each file:

  ```text
  Processing <name>.json -> <name>.txt (K unique labels)
  ```

- At end:

  ```text
  Done. Processed M files.
  ```

Without `--verbose`, only fatal or significant errors are printed.

---

## 8. Module-level docstring

`label_types.py` will include a **module-level docstring** at the top that:

1. Explains what the program does.
2. Shows basic usage.
3. Mentions that labels are lowercased and spaces are replaced by underscores.

For example (concept, not exact wording):

```python
"""
Extract unique label descriptions from Google Vision JSON responses and
write them as simple text lists.

For each input JSON file, this script writes a .txt file with one
lowercased, underscore-separated label per line.

Usage:
    python label_types.py --input-dir <INPUT_DIR> --output-dir <OUTPUT_DIR>
"""
```

This docstring will be the first statement in the module.
