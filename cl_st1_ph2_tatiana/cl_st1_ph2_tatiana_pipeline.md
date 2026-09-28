# Corpus Linguistics - Study 1 - Phase 2 - Tatiana

Run the commands from the project phase directory, e.g.:

```text
cl_st1_ph2_tatiana/
```

## 1. Find near duplicate images

```shell
python find_near_duplicates.py
```

Outputs:
- `corpus/deduplicated_2/`
- `corpus/near_duplicates/`

```shell
(my_env) eyamrog@eyamrog-Vivobook-16:~/PycharmProjects/cl_st1_tatiana/cl_st1_ph2_tatiana$ python find_near_duplicates.py
Analyzing 12983 images for similarity using parallel workers...
/home/eyamrog/anaconda3/envs/my_env/lib/python3.13/site-packages/PIL/Image.py:1137: UserWarning: Palette images with Transparency expressed in bytes should be converted to RGBA images
  warnings.warn(
/home/eyamrog/anaconda3/envs/my_env/lib/python3.13/site-packages/PIL/Image.py:1137: UserWarning: Palette images with Transparency expressed in bytes should be converted to RGBA images
  warnings.warn(
/home/eyamrog/anaconda3/envs/my_env/lib/python3.13/site-packages/PIL/Image.py:1137: UserWarning: Palette images with Transparency expressed in bytes should be converted to RGBA images
  warnings.warn(
/home/eyamrog/anaconda3/envs/my_env/lib/python3.13/site-packages/PIL/Image.py:1137: UserWarning: Palette images with Transparency expressed in bytes should be converted to RGBA images
  warnings.warn(
/home/eyamrog/anaconda3/envs/my_env/lib/python3.13/site-packages/PIL/Image.py:1137: UserWarning: Palette images with Transparency expressed in bytes should be converted to RGBA images
  warnings.warn(
/home/eyamrog/anaconda3/envs/my_env/lib/python3.13/site-packages/PIL/Image.py:1137: UserWarning: Palette images with Transparency expressed in bytes should be converted to RGBA images
  warnings.warn(
/home/eyamrog/anaconda3/envs/my_env/lib/python3.13/site-packages/PIL/Image.py:1137: UserWarning: Palette images with Transparency expressed in bytes should be converted to RGBA images
  warnings.warn(
/home/eyamrog/anaconda3/envs/my_env/lib/python3.13/site-packages/PIL/Image.py:1137: UserWarning: Palette images with Transparency expressed in bytes should be converted to RGBA images
  warnings.warn(
Analysis complete. Sorting files...

--- Summary ---
Processed: 12983 files
Unique images moved to 'corpus/deduplicated_2': 12258
Near-duplicates moved to 'corpus/near_duplicates': 725
(my_env) eyamrog@eyamrog-Vivobook-16:~/PycharmProjects/cl_st1_tatiana/cl_st1_ph2_tatiana$ 
```

> User:
>
> Are those warnings of consequence?

AI Assistant:

Probably **not serious**, given your run completed successfully:

- **Processed:** 12,983 files
- **Unique:** 12,258
- **Near-duplicates:** 725
- No crash or skipped-summary error occurred.

The warning:

```plain text
UserWarning: Palette images with Transparency expressed in bytes should be converted to RGBA images
```

comes from **Pillow/PIL**. It usually means some PNG/GIF-style images use a palette-based color mode with transparency metadata, and Pillow is warning that transparency handling is more correct if the image is converted to `RGBA`.

In your case, the script converts images to grayscale with:

```python
img.convert('L')
```

For perceptual hashing / near-duplicate detection, this is usually acceptable because transparency and color are being discarded anyway. So the warning is mostly informational.

However, it could matter if:

1. Some images have important content encoded through transparency.
2. Transparent backgrounds affect the visual appearance you care about.
3. You want the hash to match how the image looks when composited on a background.
4. You see unexpected duplicate/non-duplicate results among transparent PNGs.

If you want to silence the warning and handle those images more explicitly, convert palette/transparency images to `RGBA` before grayscale conversion, optionally compositing them over a background. For example:

```python
with Image.open(image_path) as img:
    if img.mode == "P" and "transparency" in img.info:
        img = img.convert("RGBA")

    img = img.convert("L").resize((hash_size + 1, hash_size), Image.Resampling.LANCZOS)
```

So: **not a failure, not likely consequential for a rough grayscale perceptual hash**, but worth fixing if transparent PNG accuracy matters.

### Find all subdirectories in `corpus/near_duplicates` that contain more than one file

```shell
(my_env) eyamrog@eyamrog-Vivobook-16:~/PycharmProjects/cl_st1_tatiana/cl_st1_ph2_tatiana$ find corpus/near_duplicates -mindepth 1 -type d | while read dir; \
 do [ $(ls -1A "$dir" | wc -l) -gt 1 ] && echo "$dir"; done
corpus/near_duplicates/1100110011011100110101001101110001001110000100110011001100110011
corpus/near_duplicates/1100110011010110110101001001010001110001101100101100001011010010
corpus/near_duplicates/1101001111111010111111001111010011100100110010001111100011111000
corpus/near_duplicates/0111111011011001010110010101110111011101100111011001110110011100
corpus/near_duplicates/1100110011001101110011011100110011000111000100111001000110010001
corpus/near_duplicates/1101000011000110110110101111101010110000111011001100100011111000
corpus/near_duplicates/1111110000110011110011001110100011100000111111001111000011110000
corpus/near_duplicates/0100110100110011100010110001101101010001110000110010001101011010
corpus/near_duplicates/1111000000111100001111001001011010110110001100110111001101100001
corpus/near_duplicates/1110101011110011111100011111001111100111110001001100010011000100
corpus/near_duplicates/1100110011100100111110011011100010110000101001011011111100110011
corpus/near_duplicates/1101100000011000001001000011110000111100001111000110011001100011
corpus/near_duplicates/1000111000001101011100111100100110010001100010100101110001011110
corpus/near_duplicates/1111101011110010101100001011010010110000001101101111011011011000
corpus/near_duplicates/1011001010110010101100001011101001101110111001100110001010110010
corpus/near_duplicates/1001110010110100111001001011010010110111001100110011000101110001
corpus/near_duplicates/1111010011110101011010010010110101101001010010010111100101111001
corpus/near_duplicates/1111010011111101110111101101111010011110000110100000110001001100
corpus/near_duplicates/0111001100110001011010010100100001001100010111100011101000100011
corpus/near_duplicates/1111100111110001111110111100011111100101011000011110001111000001
corpus/near_duplicates/1011100010101000011010001111001011011110110011101110001111100011
corpus/near_duplicates/1111000111011001011010000110110001101100001010000010110110000001
corpus/near_duplicates/1110011001101101110101101101000110011100111110001100100010000110
corpus/near_duplicates/0111100101111000111110011110010110000100101001100000110100011100
corpus/near_duplicates/1111110111001011100110111001101011011111001101111000011101000111
corpus/near_duplicates/1100000011010010111100101111100010001100110001000000001100000001
corpus/near_duplicates/1001100111110011110100111101011111100111111001111110011110111111
corpus/near_duplicates/0000111100100111011001011101001111100011111100111110001111100011
corpus/near_duplicates/1001111001001011001110111011011111100110110001101001111000111011
corpus/near_duplicates/1101110001011110100110101101110000111100001100000001110010100100
corpus/near_duplicates/1010110010101100101011001010110011001110100001110001010101000101
corpus/near_duplicates/1100000011010000110110001101011010011110111100101111001010000000
corpus/near_duplicates/1011000000110000001100000010010010010110110011000100110000001001
corpus/near_duplicates/0011000000110100011110101111001110110110101001101110010111101101
corpus/near_duplicates/0011001011110001110111001101100011011100110110001111100100110011
corpus/near_duplicates/1111000011111000111010001110100011101100111010001111100011110000
corpus/near_duplicates/1100110011000100110011001100110010010011001100111011001111001011
corpus/near_duplicates/1011001001100100111100011111000010100110001010110111010101111100
corpus/near_duplicates/0000100001011000100000101001001011010000011100100111001001110100
corpus/near_duplicates/1111010111110001001011010110110101101001010010010111100101111001
corpus/near_duplicates/1000000000100000110110101101011010010110110100000010100110010000
corpus/near_duplicates/1111110001110000111100001111110011111110110110000111100011111000
corpus/near_duplicates/0011111001011011110010111100001111000100110001001100110001001000
corpus/near_duplicates/1101001011010010110110111101100111010001011000010110010101100101
corpus/near_duplicates/1001111111011010100011111000110100001111010011000110110010110100
corpus/near_duplicates/0001001101100011011001110010111110101101101011011010000011000100
corpus/near_duplicates/1011100111110100111111000011111000111100001110000111100011110001
corpus/near_duplicates/1100110101100101100101101001000100011011100010111100101101001101
corpus/near_duplicates/1100000011010010111100101111100010001100110011000000001100000001
corpus/near_duplicates/1110010001111001001100011000100001011101110011011001100111000101
corpus/near_duplicates/1110000111111000101110000011100011111000101110101111000011111100
corpus/near_duplicates/1001010110011000100100111011100110001100100111001011110010110000
corpus/near_duplicates/1111000011110000111110001110100011101000111110001111000011110000
corpus/near_duplicates/1110100010010100100001101000101011001110111001101100111110011001
corpus/near_duplicates/1100001011000011110010111100110111000010110000101100000011001001
corpus/near_duplicates/0111011101100011010100110101001101000011000100110101001100010011
corpus/near_duplicates/1111001011110011111101011111000111110001110001001100110011001100
corpus/near_duplicates/1111100011111000111011001110110011101100111011001111100011111000
corpus/near_duplicates/0111001101100001110100011110000111101000111000100110011000100110
corpus/near_duplicates/1001100010011000101000001111100110110001111000001100011011101100
corpus/near_duplicates/0010100000010100011100000111000101100001001010000011001000001000
corpus/near_duplicates/0011011000110110011000100010011000100111111000001110010010100100
corpus/near_duplicates/0111100111100001110000010101110000001100110111000111100111001100
corpus/near_duplicates/0010110100001101100101110111011101110111101001100111001111110011
corpus/near_duplicates/1000110010010100100101001001010010010110001100100011010000110100
corpus/near_duplicates/1110011011100010111010101110011011001011100110011001100110011001
corpus/near_duplicates/0111000001001010010110100000111001001001110110011111100111100111
corpus/near_duplicates/0100110101100100110010100001100000010101001100110011000101100000
corpus/near_duplicates/1001110011010000010100001100000011000000110010001100000110100101
corpus/near_duplicates/1001100111001001010011010000110000111000001001110011110000111000
corpus/near_duplicates/1100000001101001011000010011000001011101110101011111010011000100
corpus/near_duplicates/0001100011000010101100100011100000111000001100100001101001001100
corpus/near_duplicates/1000001110100011001000111110001111000011110000111101110011111010
corpus/near_duplicates/1111010011111101110111101101111010011110100110100000110001001100
corpus/near_duplicates/1110001010110010001100010111000101000001010001110101101100011011
corpus/near_duplicates/0010110000001101100101110111011101110111101001100111001111110011
corpus/near_duplicates/1111001001110000011110000101110011011001110101110100100111001101
corpus/near_duplicates/1000000110101001001011010000110110101010110010110100000111000001
corpus/near_duplicates/1110000011100000011101000111100001111010011111100011110001110000
corpus/near_duplicates/1010101010100011101001011010010010001100101001011000000110000100
corpus/near_duplicates/1101100010111100101101001111110011011000101100100101100011011010
corpus/near_duplicates/0010011101010001010111011111011001010001011100001011100010110110
corpus/near_duplicates/1111100011111100110111101101111010011110100110100000111000001100
corpus/near_duplicates/1001011010011011010110110101100000110101101001011011010111110010
corpus/near_duplicates/0101110001011000100100101011001011011010110100101010000010010001
corpus/near_duplicates/0011100100110001011010010110100101101001011010010110100100001111
corpus/near_duplicates/1101000011010010000100001010000110101011010011100011100011100010
corpus/near_duplicates/1111001111110010000001010000110111011101100011000010011100100011
corpus/near_duplicates/1100110011000100111010011011100010110000101001011011111100110011
corpus/near_duplicates/1101100011101100111100101011000011110110111100101010100001010100
corpus/near_duplicates/0110010001101100011001100110100101100001011001010110100101101100
corpus/near_duplicates/1111010011110001001011010110110101101001010010010111100101111001
corpus/near_duplicates/1001001110010010011100111011001110011001110110011111001100010010
corpus/near_duplicates/1101001011010100110101001101000011010100100101001110010011110100
corpus/near_duplicates/1101111011001100110011001100100111010001111100001111010111010000
corpus/near_duplicates/0000001100100011000100110001001100010111001011010000110000011000
corpus/near_duplicates/0001111101011011110110011001110010011100100111001001101110011111
corpus/near_duplicates/1010010001110010110001011110011001001000000010000001110101010100
corpus/near_duplicates/1110110011110000111010001100010011000100111000001111000011011000
corpus/near_duplicates/1011001001110000011111000101100011011001110101110100100111000101
corpus/near_duplicates/0100011111010110110100101001101110011011110010101111100011100100
corpus/near_duplicates/1011101011010010110100001111000011110000111100001101000001101000
corpus/near_duplicates/1100101111001011111000001010101010000010111000001010010011000010
corpus/near_duplicates/0101001111100000111001001000110010110100111010101111000000011001
corpus/near_duplicates/1111000011011000110110001100100011000110110001111101001111000011
corpus/near_duplicates/1100110011100100111110011011100010010000101001011011111100110011
corpus/near_duplicates/1010110010101110111011100010011001101110011010010110100101000001
corpus/near_duplicates/0100111001001100010101000001010000010110000110100010101100100011
corpus/near_duplicates/0110101111110010111000101100010011001100111011001100111011101100
corpus/near_duplicates/1111000011110000111100001110010011111100111100011100001111001110
corpus/near_duplicates/1110110011000010110001111000011110000111101001100000111100011001
corpus/near_duplicates/1001100010011000101011000010110000101100001011000110011001110110
corpus/near_duplicates/0011101101110100010111000111010001110000010110000001100110011011
corpus/near_duplicates/1111000011110000111110001111100011101000111110001111000011110000
corpus/near_duplicates/1100000011010010111100101111100010011100110011001000011000000011
corpus/near_duplicates/1011110000101000011100001111111011001111111000111110101111101010
corpus/near_duplicates/1100100011011100110110001001011000110110001101100111000011110000
corpus/near_duplicates/1111100001011110011111111011101111101010101001101000111011001110
corpus/near_duplicates/1110100011110010111100111110111011011011100110111100101111000010
corpus/near_duplicates/1111110001011110101100111010101011100110100011101100110011110000
corpus/near_duplicates/0010110010110001111111011100111111000111111100011111000111100101
corpus/near_duplicates/0110100011110010110011101100111111100011111000111110101011101011
corpus/near_duplicates/1111001001110000011111000101100011010011110100110100010111000001
corpus/near_duplicates/0001101000010100011001010110010111000110000100110101001111000111
corpus/near_duplicates/0110011011001110110010111110000011101100110010010001100000110011
corpus/near_duplicates/1110000111001001010010010010110110110100101101000010010011100110
corpus/near_duplicates/0110001111100111110001011101100110010100110111000001110000011100
corpus/near_duplicates/1101100011110000111100001111000011100100111100011100000111001110
(my_env) eyamrog@eyamrog-Vivobook-16:~/PycharmProjects/cl_st1_tatiana/cl_st1_ph2_tatiana$ 
```

## 2. Detect labels

### Dry run

```shell
python detect_labels.py \
    --input-dir corpus/deduplicated_2 \
    --output-dir corpus/02_labelled \
    --dry-run
```

Output: `corpus/02_labelled/`

### Production mode on an EC2 instance

```shell
bash run_python_ec2.sh \
    detect_labels.py \
    --input-dir corpus/deduplicated_2 \
    --output-dir corpus/02_labelled
```

There were 389 files with empty JSON outputs:

- `corpus/label_empty.tsv`

Therefore, a `retry` functionality was added to the `detect_label.py` programme.

### File-based retry

```shell
python detect_labels.py \
  --input-dir corpus/deduplicated_2 \
  --output-dir corpus/02_labelled \
  --retry-file corpus/02_labelled/saude202003_n_00026_00000004.json \
  --retry-file corpus/02_labelled/saude202003_n_00027_00000004.json \
  --force
```

Note: In retry mode, treat `--force` as effectively implied, because the point is to overwrite the existing empty/failed JSON outputs. The code does that by bypassing the normal “skip existing output” filter when retrying from `label_empty.tsv`.

### List-based retry

#### Specific files retry

```shell
python detect_labels.py \
  --input-dir corpus/deduplicated_2 \
  --output-dir corpus/02_labelled \
  --retry-empty-tsv corpus/label_empty.tsv \
  --retry-file saude202003_n_00026_00000004 \
  --retry-file saude202003_n_00027_00000004 \
  --force
```

#### Full retry

```shell
python detect_labels.py \
  --input-dir corpus/deduplicated_2 \
  --output-dir corpus/02_labelled \
  --retry-empty-tsv corpus/label_empty.tsv \
  --force
```

The retry resulted in the same empty JSON outputs as can be seen below. Therefore, they will be automatically removed from the statistical analysis (SAS) as `lines that are all zeros`.

```shell
ubuntu@ip-172-31-5-110:~/cl_st1_tatiana/cl_st1_ph2_tatiana$ python detect_labels.py \
  --input-dir corpus/deduplicated_2 \
  --output-dir corpus/02_labelled \
  --retry-empty-tsv corpus/label_empty.tsv \
  --force
[INFO] Using 1 input directory(ies).
[INFO] Loading environment variables from env/.env
[INFO] Using explicit Google Cloud project: cl-st1-tatiana
[INFO] Loaded 389 retry filepath(s) from corpus/label_empty.tsv.
[INFO] Built 389 retry task(s).
[INFO] Retry mode enabled from TSV: 389 image(s) selected for reprocessing.
[INFO] Processed 10/389 images
[INFO] Processed 20/389 images
[INFO] Processed 30/389 images
[INFO] Processed 40/389 images
[INFO] Processed 50/389 images
[INFO] Processed 60/389 images
[INFO] Processed 70/389 images
[INFO] Processed 80/389 images
[INFO] Processed 90/389 images
[INFO] Processed 100/389 images
[INFO] Processed 110/389 images
[INFO] Processed 120/389 images
[INFO] Processed 130/389 images
[INFO] Processed 140/389 images
[INFO] Processed 150/389 images
[INFO] Processed 160/389 images
[INFO] Processed 170/389 images
[INFO] Processed 180/389 images
[INFO] Processed 190/389 images
[INFO] Processed 200/389 images
[INFO] Processed 210/389 images
[INFO] Processed 220/389 images
[INFO] Processed 230/389 images
[INFO] Processed 240/389 images
[INFO] Processed 250/389 images
[INFO] Processed 260/389 images
[INFO] Processed 270/389 images
[INFO] Processed 280/389 images
[INFO] Processed 290/389 images
[INFO] Processed 300/389 images
[INFO] Processed 310/389 images
[INFO] Processed 320/389 images
[INFO] Processed 330/389 images
[INFO] Processed 340/389 images
[INFO] Processed 350/389 images
[INFO] Processed 360/389 images
[INFO] Processed 370/389 images
[INFO] Processed 380/389 images
[INFO] Processed 389/389 images
[INFO] Processing complete. Success: 389, Failed: 0, Skipped (existing): 0, Total discovered/selected: 389
ubuntu@ip-172-31-5-110:~/cl_st1_tatiana/cl_st1_ph2_tatiana$ git status
On branch main
Your branch is up to date with 'origin/main'.

nothing to commit, working tree clean
ubuntu@ip-172-31-5-110:~/cl_st1_tatiana/cl_st1_ph2_tatiana$ 
```

## 3. Extract key lemmas by group

```shell
python keylemmas.py \
  --input corpus/07_tagged \
  --output corpus/08_keylemmas \
  --cutoff 3
```

Output: `corpus/08_keylemmas/<group>.tsv`

## 4. Select a stratified keyword set

```shell
python select_kws_stratified.py \
    --input corpus/08_keylemmas \
    --output corpus/09_kw_selected \
    --per-group 45 \
    --max-total 20000
```

Output: `corpus/09_kw_selected/keywords.txt

Deprecated run

```shell
=== Stratum Keyword Quotas ===
ac                     → 45 keywords max
al                     → 45 keywords max
am                     → 45 keywords max
ap                     → 45 keywords max
ba                     → 45 keywords max
ce                     → 45 keywords max
df                     → 45 keywords max
es                     → 45 keywords max
go                     → 45 keywords max
ma                     → 45 keywords max
mg                     → 45 keywords max
ms                     → 45 keywords max
mt                     → 45 keywords max
pa                     → 45 keywords max
pb                     → 45 keywords max
pe                     → 45 keywords max
pi                     → 45 keywords max
pr                     → 45 keywords max
rj                     → 45 keywords max
rn                     → 45 keywords max
ro                     → 45 keywords max
rr                     → 45 keywords max
rs                     → 45 keywords max
sc                     → 45 keywords max
se                     → 45 keywords max
sp                     → 45 keywords max
to                     → 45 keywords max
==============================

ac                     → selected 45/45 from 246 available POSKW lemmas
al                     → selected 45/45 from 89 available POSKW lemmas
am                     → selected 45/45 from 170 available POSKW lemmas
ap                     → selected 43/45 from 43 available POSKW lemmas
ba                     → selected 45/45 from 355 available POSKW lemmas
ce                     → selected 45/45 from 366 available POSKW lemmas
df                     → selected 45/45 from 120 available POSKW lemmas
es                     → selected 45/45 from 124 available POSKW lemmas
go                     → selected 45/45 from 364 available POSKW lemmas
ma                     → selected 45/45 from 244 available POSKW lemmas
mg                     → selected 30/45 from 30 available POSKW lemmas
ms                     → selected 45/45 from 147 available POSKW lemmas
mt                     → selected 45/45 from 252 available POSKW lemmas
pa                     → selected 45/45 from 678 available POSKW lemmas
pb                     → selected 45/45 from 140 available POSKW lemmas
pe                     → selected 45/45 from 68 available POSKW lemmas
pi                     → selected 45/45 from 189 available POSKW lemmas
pr                     → selected 45/45 from 853 available POSKW lemmas
rj                     → selected 45/45 from 121 available POSKW lemmas
rn                     → selected 45/45 from 74 available POSKW lemmas
ro                     → selected 45/45 from 110 available POSKW lemmas
rr                     → selected 45/45 from 65 available POSKW lemmas
rs                     → selected 45/45 from 91 available POSKW lemmas
sc                     → selected 45/45 from 1147 available POSKW lemmas
se                     → selected 45/45 from 159 available POSKW lemmas
sp                     → selected 45/45 from 98 available POSKW lemmas
to                     → selected 45/45 from 102 available POSKW lemmas

Total consolidated keywords before de-duplication: 1198
Unique keywords after de-duplication: 1061
Duplicates removed: 137

Final unique keywords written to: corpus/09_kw_selected/keywords.txt
Final unique keyword count: 1061
```

Current run

```shell
=== Stratum Keyword Quotas ===
ac                     → 45 keywords max
al                     → 45 keywords max
am                     → 45 keywords max
ap                     → 45 keywords max
ba                     → 45 keywords max
ce                     → 45 keywords max
df                     → 45 keywords max
es                     → 45 keywords max
go                     → 45 keywords max
ma                     → 45 keywords max
mg                     → 45 keywords max
ms                     → 45 keywords max
mt                     → 45 keywords max
pa                     → 45 keywords max
pb                     → 45 keywords max
pe                     → 45 keywords max
pi                     → 45 keywords max
pr                     → 45 keywords max
rj                     → 45 keywords max
rn                     → 45 keywords max
ro                     → 45 keywords max
rr                     → 45 keywords max
rs                     → 45 keywords max
sc                     → 45 keywords max
se                     → 45 keywords max
sp                     → 45 keywords max
to                     → 45 keywords max
==============================

ac                     → selected 45/45 from 226 available POSKW lemmas
al                     → selected 45/45 from 75 available POSKW lemmas
am                     → selected 45/45 from 147 available POSKW lemmas
ap                     → selected 33/45 from 33 available POSKW lemmas
ba                     → selected 45/45 from 294 available POSKW lemmas
ce                     → selected 45/45 from 329 available POSKW lemmas
df                     → selected 45/45 from 93 available POSKW lemmas
es                     → selected 45/45 from 107 available POSKW lemmas
go                     → selected 45/45 from 324 available POSKW lemmas
ma                     → selected 45/45 from 215 available POSKW lemmas
mg                     → selected 22/45 from 22 available POSKW lemmas
ms                     → selected 45/45 from 122 available POSKW lemmas
mt                     → selected 45/45 from 215 available POSKW lemmas
pa                     → selected 45/45 from 605 available POSKW lemmas
pb                     → selected 45/45 from 116 available POSKW lemmas
pe                     → selected 45/45 from 52 available POSKW lemmas
pi                     → selected 45/45 from 157 available POSKW lemmas
pr                     → selected 45/45 from 781 available POSKW lemmas
rj                     → selected 45/45 from 106 available POSKW lemmas
rn                     → selected 45/45 from 64 available POSKW lemmas
ro                     → selected 45/45 from 102 available POSKW lemmas
rr                     → selected 45/45 from 53 available POSKW lemmas
rs                     → selected 45/45 from 76 available POSKW lemmas
sc                     → selected 45/45 from 1088 available POSKW lemmas
se                     → selected 45/45 from 130 available POSKW lemmas
sp                     → selected 45/45 from 91 available POSKW lemmas
to                     → selected 45/45 from 94 available POSKW lemmas

Total consolidated keywords before de-duplication: 1180
Unique keywords after de-duplication: 1037
Duplicates removed: 143

Final unique keywords written to: corpus/09_kw_selected/keywords.txt
Final unique keyword count: 1037
```

## 5. Build binary keyword columns

```shell
rm -rf columns columns_clean
```

```shell
python columns.py
```

Outputs:
- `columns/`
- `columns_clean/`
- `file_ids.txt`
- `index_keywords.txt`

## 6. Merge columns into the SAS counts matrix

```shell
python merge_columns.py
```

Output: `sas/counts.txt`

## 7. Generate SAS format files

```shell
python sas_formats.py
```

Outputs:

- sas/word_labels_format.sas
- sas/word_labels_full_format.sas
- other SAS helper format files

## 8. Run SAS

## 9. Build factor loading lists

```shell
python factor_lists.py
```

Output: factors/

## 10. Calculate corpus size summaries

```shell
python corpus_size.py
```

Output: `corpus_size/corpus_size.tsv`

## 11. Generate LaTeX/TikZ boxplots

```shell
cd latex_boxplots
```

```shell
python latex_boxplots.py
```

Output: `latex_boxplots/slides/`

```shell
cd ..
```

## 12. Generate LaTeX ANOVA table

```shell
python latex_anova_table.py
```

Output: `latex_tables/anova_state.tex`

## 13. Generate LaTeX example extracts

```shell
python examples.py
```

Output: `examples/`

## 14. Generate score-details report

```shell
python score_details.py
```

Output: `examples/score_details.txt`

## 15. Generate plaintext example extracts

The `examples_txt.py` programme was affected by a bug that has been fixed as reported in:

- [examples_txt_bug_report.md](https://github.com/laelgelc/cl_st1_anna/blob/main/cl_st1_ph2_anna/examples_txt_bug_report.md); or
- `examples_txt_bug_report.md`

```shell
python examples_txt.py
```

Output: `examples_txt/`

## 16. Build interpretation prompts

```shell
python interpretation_prompts.py
```

Output: `interpretation/input/`

## 17. Submit interpretation prompts to GPT

```shell
python generate_interpretation_gpt.py \
    --input interpretation/input \
    --output interpretation/output \
    --model gpt-6-sol \
    --workers 4
```
Output: `interpretation/output/`
