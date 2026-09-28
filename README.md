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

- Prepared the tweet verbal and visual subcorpora for Canonical Correlation Analysis (CCA).
- Loaded verbal factor scores from the verbal MDA output and renamed the verbal dimensions from `fac<n>` to `ver<n>`.
- Loaded tweet metadata from `corpus/tweets.ndjson` and mapped verbal score rows to their corresponding image identifiers.
- Loaded visual factor scores from the Phase 2 visual MDA output and renamed the visual dimensions from `fac<n>` to `vis<n>`.
- Mapped visual image filenames back to verbal tweet file identifiers.
- Checked alignment between the verbal and visual score datasets.
- Created the CCA-ready merged dataset by retaining only tweets/images present in both modalities.
- Saved the merged CCA dataset as:
  - `corpus/tweets_cca.ndjson`
  - `corpus/tweets_cca.xlsx`
  - `corpus/tweets_cca.tsv`
- Imported and verified CCA results for:
  - correlations between verbal variables and their canonical variables;
  - correlations between visual variables and their canonical variables.
- Extracted statistically interpretable canonical structure loadings for the first five canonical dimensions using a loading cutoff of `|.30|`.
- Saved canonical-dimension loading data as:
  - `corpus/tweets_cca_dimension_loadings.ndjson`
  - `corpus/tweets_cca_dimension_loadings.xlsx`
  - `corpus/tweets_cca_dimension_loadings.tsv`
- Generated LaTeX tables for each canonical dimension in:
  - `corpus/tables/cca_dimension_loadings/`
- Generated paired verbal/visual loading charts for each canonical dimension in:
  - `corpus/figures/cca_dimension_loadings/`
- Interpreted the first five canonical dimensions as cross-modal discursive patterns linking verbal MDA dimensions with visual MDA dimensions:
  - Canonical dimension 1 captures an opposition between a `ver1`/`ver4` verbal profile aligned with `vis4` imagery and a `ver2` verbal profile aligned with `vis2` imagery.
  - Canonical dimension 2 links a combined `ver1`/`ver2` verbal profile to a coherent visual pattern centred on `vis7`, with secondary contributions from `vis6` and `vis2`.
  - Canonical dimension 3 associates a `ver4`-centred verbal profile with `vis2`/`vis7`/`vis5` imagery, in contrast to a visually distinct `vis6` pole.
  - Canonical dimension 4 contrasts a `ver4` verbal orientation associated with `vis3`/`vis5`/`vis2` imagery against a `ver3`/`ver5` verbal orientation associated with the opposite `vis7` pole.
  - Canonical dimension 5 captures a focused `ver6` verbal profile associated with `vis2` imagery and opposed to a visual cluster marked by `vis5`, `vis1`, and `vis3`.

Please refer to []() or `cl_st1_ph3_tatiana/cca_interpretation.md`
