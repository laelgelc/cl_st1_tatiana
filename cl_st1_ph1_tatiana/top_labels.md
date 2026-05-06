## Specification: `top_labels.py` – Top Label Aggregation

### Purpose

`top_labels.py` aggregates label frequencies from a directory of label files and writes:

1. `top_labels_counts.txt` – each label with its overall count.
2. `top_labels.txt` – the top 1,000 labels only (no counts).

Labels are sorted by descending frequency.

---

### Module-level docstring (required)

At the top of `top_labels.py`, include a docstring that:

- Explains what the script does.
- Describes its command-line interface and outputs.
- Is suitable as both in-code documentation and quick usage reference.

Example docstring you can use or adapt:

```python
"""Aggregate label frequencies from label files and write top-label reports.

Overview
========
This script scans an input directory containing text files with labels, counts how
often each label occurs across all files, and writes two summary files:

* ``top_labels_counts.txt`` – all distinct labels with their total counts, one per line:
  
  ``<label> <count>``

  Lines are sorted in descending order of ``count`` (and optionally by label as a
  tie-breaker for deterministic output).

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
  files under this directory (e.g. ``.txt`` files) and extracts labels from them.

* ``--output-dir DIR``

  Directory where the output files will be written:
  ``top_labels_counts.txt`` and ``top_labels.txt``. The directory is created if it
  does not already exist. Existing files with these names may be overwritten.

Processing Summary
==================
1. Discover and read all label files from ``--input-dir``.
2. Parse labels from each file (for example, one label per line, ignoring empty lines).
3. Maintain a global counter ``label -> total occurrences`` across all files.
4. Sort labels primarily by descending count, and optionally by label name as a
   deterministic tie-breaker.
5. Write the full sorted list with counts to ``top_labels_counts.txt``.
6. Write the first 1,000 labels (or fewer, if not enough labels) without counts to
   ``top_labels.txt``.
"""
```

You can tighten the parts about input format to exactly match how your label files are structured.

---

### Command line interface

```bash
python top_labels.py \
    --input-dir <INPUT_DIR> \
    --output-dir <OUTPUT_DIR>
```

**Arguments:**

- `--input-dir` (required)  
  Path to a directory containing the label files to be processed.

- `--output-dir` (required)  
  Path to a directory where output files will be written.  
  - If it does not exist, it should be created.
  - Existing files with the same names may be overwritten.

---

### Input format

- The program reads all relevant files from `--input-dir` (e.g. all `.txt` files; your implementation should define this precisely).
- Each file contains labels (for instance, one label per line).
- Empty lines and surrounding whitespace in a label line should be ignored.
- Labels are taken exactly as strings (no case-folding, unless you explicitly define that).

The script counts how many times each label occurs **across all files**.

---

### Processing logic

1. Traverse all label files in `--input-dir`.
2. For each file:
   - Parse labels according to the chosen format.
   - Normalize them as required (e.g. `strip()`).
   - Update a global counter `label → count`.
3. After processing all files, sort labels:
   - Primary key: count, descending.
   - Secondary key (optional but recommended): label, ascending (for deterministic output).

---

### Output files

All files go into `--output-dir`.

#### `top_labels_counts.txt`

- Contains all distinct labels.
- Format: one label per line, followed by a space and its count.

  ```text
  <label> <count>
  ```

- Ordered using the global sort (descending count).

Example (format only):

```text
Commercial building 1234
Headquarters 987
Science 850
...
```

#### `top_labels.txt`

- Contains only labels (no counts).
- Includes the first 1,000 labels of the same sorted sequence used for `top_labels_counts.txt`.
- If total distinct labels < 1,000, include all.

Format:

```text
<label>
```

Example (format only):

```text
Commercial building
Headquarters
Science
...
```

---

### Error handling (recommended)

- If `--input-dir` does not exist or is not a directory: exit with a clear error message.
- If there are no usable label files:
  - Either create empty output files, or exit with a descriptive message (document which behavior you choose).
- If `--output-dir` does not exist: create it (including parents if needed).
