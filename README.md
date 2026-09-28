# Corpus Linguistics - Study 1 - Tatiana

## Phase 0
- Detection of corrupt images and duplicates.

## Phase 1
- Visual Multi-dimensional Analysis considering image tagging with Google Cloud Vision API.

## Phase 2 - Visual Multi-dimensional Analysis
- Deduplicated the image corpus for the second phase of the study.
- Processed 12,983 images for near-duplicate detection.
- Retained 12,258 unique images in `corpus/deduplicated_2/`.
- Separated 725 near-duplicate images into `corpus/near_duplicates/`.
- Detected image labels for the deduplicated corpus using Google Cloud Vision API.
- Stored raw Vision API label outputs as JSON files in `corpus/02_labelled/`.
- Identified 389 empty label-output files and recorded them in `corpus/label_empty.tsv`.
- Added and used retry functionality for empty or failed label-detection outputs.
- Confirmed that retrying the 389 empty outputs completed successfully, but the outputs remained empty.
- Removed persistently empty label outputs from the statistical-analysis workflow using the Phase 2 notebook.
- Extracted label types from the raw Vision outputs into `corpus/03_label_types/`.
- Identified top image labels for analysis in `corpus/04_top_labels/`.
- Built binary top-label columns for the visual MDA input matrix.
- Generated:
    - `columns/`
    - `columns_clean/`
    - `file_ids.txt`
    - `index_top_labels.txt`
- Merged cleaned label columns into the SAS counts matrix at `sas/counts.txt`.
- Generated SAS format/helper files, including:
    - `sas/word_labels_format.sas`
    - `sas/word_labels_full_format.sas`
- Ran the external SAS workflow for the visual multi-dimensional analysis.
- Generated post-SAS factor loading lists in `factors/`.
- Calculated corpus-size summaries in `corpus_size/corpus_size.tsv`.
- Generated LaTeX example extracts in `examples/`.
- Produced a score-details sanity-check report at `examples/score_details.txt`.
- Generated plaintext example extracts in `examples_txt/`.

See `cl_st1_ph2_tatiana/cl_st1_ph2_tatiana_pipeline.md` for the detailed Phase 2 run log and commands.

## Phase 3 - Canonical Correlation Analysis
