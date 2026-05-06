# Specification: `columns.py` adaptation

## 1. Purpose

Adapt `columns.py` so that it:

- Uses **top labels** (from `top_labels.txt`) as the “keywords”.
- Uses **label files** in `corpus/03_label_types` as the only corpus.
- Produces:
  - Per-label **column files** in `columns/` with one row per file: `file_id has_kw`.
  - **Clean column files** in `columns_clean/` with only binary values (plus a header).
  - An **index** mapping label IDs to label strings.
  - A **file ID list** mapping internal IDs to corpus filenames.

The script is still run as a simple script from the project root (no CLI args).

---

## 2. Configuration (Updated)

Replace the configuration block with:

```python
# === Configuration ===
KEYWORD_FILE = Path("corpus/04_top_labels/top_labels.txt")
TAGGED_BASE  = Path("corpus/03_label_types")
OUTPUT_DIR   = Path("columns")
CLEAN_DIR    = Path("columns_clean")
INDEX_FILE   = Path("index_top_labels.txt")
FILE_IDS     = Path("file_ids.txt")   # <-- renamed
```

- `KEYWORD_FILE`: list of labels (one per line) from `top_labels.py`.
- `TAGGED_BASE`: directory with per-image label files (`*.txt`).
- `OUTPUT_DIR`: destination for raw column files.
- `CLEAN_DIR`: destination for “clean” binary-only columns.
- `INDEX_FILE`: mapping from numeric label IDs to label strings.
- `FILE_IDS`: mapping from file IDs to `.txt` files in `TAGGED_BASE`.

---

## 3. Input Formats and Assumptions

### 3.1 Keywords (`KEYWORD_FILE`)

- UTF-8 text file.
- One label per line, e.g.:

  ```text
  science
  screenshot
  health_care
  ...
  ```

- Empty / whitespace-only lines are ignored.
- The script:
  1. Reads non-empty lines.
  2. Deduplicates (`set`).
  3. Sorts lexicographically to get a stable order:

     ```python
     lemmas = sorted(set(lemmas))
     ```

### 3.2 Corpus (`TAGGED_BASE`)

- `TAGGED_BASE` exists and is a directory.
- **Current expectation:** flat directory (all `.txt` files directly under `corpus/03_label_types`).
- **Future-proofing:** implementation should be easy to switch to recursive search (e.g. replacing a single comprehension with `rglob("*.txt")`), but for now it uses non-recursive listing.

Each label file:

```text
eyewear
glasses
vision_care
news
spokesperson
screenshot
photo_caption
speech
moustache
```

- One label per line.
- Labels already normalized (lowercase, underscores).
- Empty lines allowed; must be ignored.

---

## 4. IDs and Indices

### 4.1 Label IDs

From the sorted, unique `lemmas`, build:

```python
lemma_index = {lemma: f"{i+1:06d}" for i, lemma in enumerate(lemmas)}
```

- IDs: `000001`, `000002`, …  
- Used for:
  - Column file names: `columns/<id>.txt`
  - Clean files: `columns_clean/<id>.txt`
  - First line of each clean file.
  - `INDEX_FILE` mapping.

### 4.2 File IDs (`FILE_IDS`)

Collect corpus files and assign IDs:

1. Enumerate `.txt` files in `TAGGED_BASE`:

   ```python
   text_paths = sorted(
       p for p in TAGGED_BASE.iterdir()
       if p.is_file() and p.suffix == ".txt"
   )
   ```

   (Non-recursive; one line in code can be swapped to `TAGGED_BASE.rglob("*.txt")` in future if needed.)

2. If `text_paths` is empty:
   - Print an error to stderr (e.g. `Error: no .txt files found in corpus/03_label_types`) and **exit with non-zero status**.

3. Assign file IDs in order:

   - For `i` starting at 1:

     ```python
     fid = f"t{i:06d}"
     ```

   - Write to `FILE_IDS`:

     ```text
     t000001 tweet_000002_000001.txt
     t000002 tweet_000003_000001.txt
     ...
     ```

     - First column: internal file ID.
     - Second column: file name *relative to* `TAGGED_BASE` (flat corpus: just `text_file.name`).

   - Build `file_id_map[text_file] = fid`.

---

## 5. Core Processing

### 5.1 Load and Normalize Keywords

- Read `KEYWORD_FILE` (UTF-8).
- Extract non-empty `strip()`ed lines.
- Deduplicate and sort.
- Build `lemma_index`.

If `KEYWORD_FILE` is missing or unreadable: print error and exit non-zero.

### 5.2 Read Labels for Each File

For each `text_file` in `text_paths`:

1. Get `fid = file_id_map[text_file]`.
2. Read file (UTF-8).
3. Build a `set` of labels:

   ```python
   present = set()
   for line in tf:
       label = line.strip()
       if label:
           present.add(label)
   ```

4. Store a minimal info record:

   ```python
   text_infos.append({
       "id": fid,
       "name": text_file.name,
       "labels": present,
   })
   ```

- No `source`, `prompt`, or `model`: they are dropped per simplification preference.

---

## 6. Column Files (`columns/`)

For each `lemma` in `lemmas` (in sorted order):

1. `lemma_id = lemma_index[lemma]`.
2. `outpath = OUTPUT_DIR / f"{lemma_id}.txt"`.
3. For each `info` in `text_infos` (in file ID order):

   - Determine label presence:

     ```python
     has_kw = 1 if lemma in info["labels"] else 0
     ```

   - Write a row:

     ```text
     <file_id> <has_kw>
     ```

     Example:

     ```text
     t000001 1
     t000002 0
     t000003 1
     ...
     ```

4. Ensure `OUTPUT_DIR` exists (`mkdir(exist_ok=True)`).

This is the **simplified** format you confirmed: only `file_id` and `has_kw`.

---

## 7. Index File (`index_top_labels.txt`)

Write:

```text
<label_id> <label>
```

for each `lemma` in `lemmas`, in the same order:

Example:

```text
000001 science
000002 screenshot
000003 health_care
...
```

---

## 8. Clean Column Files (`columns_clean/`)

For each `lemma`:

1. Determine `lemma_id`.
2. `src = columns/<lemma_id>.txt`, `dst = columns_clean/<lemma_id>.txt`.
3. Read `src` lines; each is `"<file_id> <has_kw>"`.
4. Write to `dst`:

   1. First line: `lemma_id`.
   2. Then, for each line in `src`:
      - Split, take the **last token** (the binary 0 or 1).
      - Write just that value on its own line.

Example:

- `columns/000001.txt`:

  ```text
  t000001 1
  t000002 0
  t000003 1
  ```

- `columns_clean/000001.txt`:

  ```text
  000001
  1
  0
  1
  ```

Ensure `CLEAN_DIR` exists (`mkdir(exist_ok=True)`).

---

## 9. Error Handling

- **Missing `KEYWORD_FILE`**: error to stderr, exit non-zero.
- **Missing or non-directory `TAGGED_BASE`**: error to stderr, exit non-zero.
- **No `.txt` files in `TAGGED_BASE`**: error to stderr, exit non-zero.
- **Unreadable individual label file**:
  - Print warning indicating failed file and exception.
  - Skip that file; continue processing others.
- **Write errors** for `FILE_IDS`, `columns/`, `columns_clean/`, or `INDEX_FILE`:
  - Print error and exit non-zero.

---

## 10. Outputs Summary

After a successful run:

- `columns/`
  - `<label_id>.txt` per label, lines: `<file_id> <has_kw>`.
- `columns_clean/`
  - `<label_id>.txt` per label:
    - Line 1: `<label_id>`.
    - Remaining: one `0`/`1` per file in `FILE_IDS` order.
- `index_top_labels.txt`
  - `<label_id> <label>` per line.
- `file_ids.txt`
  - `tNNNNNN <relative_filename>` per line, where `<relative_filename>` is `tweet_...txt` under `corpus/03_label_types`.
