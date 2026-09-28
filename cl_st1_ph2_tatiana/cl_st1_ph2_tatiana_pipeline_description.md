# cl_st1_ph2_tatiana - Pipeline Programmes

This document summarises the programmes used in the Phase 2 project pipeline. The pipeline deduplicates the image corpus, detects image labels with Google Cloud Vision, converts labels into a binary label matrix for SAS, processes post-SAS factor outputs, and generates reporting and interpretation materials.

| Step | Programme / Command            | Purpose                                                                                                                                                                                                | Main Inputs                                                               | Main Outputs                                                                                   |
|-----:|--------------------------------|--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|---------------------------------------------------------------------------|------------------------------------------------------------------------------------------------|
|    1 | `find_near_duplicates.py`      | Finds near-duplicate images using perceptual image similarity and separates unique images from near-duplicate files.                                                                                   | Source image corpus                                                       | `corpus/deduplicated_2/`; `corpus/near_duplicates/`                                            |
|    2 | `detect_labels.py`             | Calls Google Cloud Vision API `LABEL_DETECTION` for each deduplicated image and writes one raw JSON label-response file per image. Supports dry-run, retry, forced reprocessing, and parallel workers. | `corpus/deduplicated_2/`; Google Cloud credentials in `env/.env`          | `corpus/02_labelled/`                                                                          |
|    3 | `detect_labels.py` retry mode  | Reprocesses empty or failed Vision JSON outputs, either from a TSV list or from specific retry files.                                                                                                  | `corpus/label_empty.tsv`; `corpus/deduplicated_2/`; `corpus/02_labelled/` | Regenerated JSON files in `corpus/02_labelled/`                                                |
|    4 | Jupyter notebook cleanup       | Drops images with persistently empty label outputs before statistical analysis.                                                                                                                        | `corpus/02_labelled/`; empty-label file list                              | Cleaned corpus / analysis-ready label set                                                      |
|    5 | `label_types.py`               | Extracts label types from the raw Google Vision JSON outputs and writes intermediate label-type files.                                                                                                 | `corpus/02_labelled/`                                                     | `corpus/03_label_types/`                                                                       |
|    6 | `top_labels.py`                | Identifies the most relevant or frequent image labels to use as variables in the visual MDA matrix.                                                                                                    | `corpus/03_label_types/`                                                  | `corpus/04_top_labels/`; `index_top_labels.txt`                                                |
|    7 | `rm -rf columns columns_clean` | Removes previously generated label-column folders before rebuilding them, ensuring that the column matrix matches the latest top-label list.                                                           | Existing `columns/` and `columns_clean/` directories, if present          | Clean workspace for regenerated columns                                                        |
|    8 | `columns.py`                   | Builds binary top-label columns for each image and writes file and label index mappings.                                                                                                               | `corpus/04_top_labels/`; labelled image data                              | `columns/`; `columns_clean/`; `file_ids.txt`; `index_top_labels.txt`                           |
|    9 | `merge_columns.py`             | Merges the per-image binary label columns into the space-separated counts matrix required by the SAS LMDA workflow.                                                                                    | `columns_clean/`                                                          | `sas/counts.txt`                                                                               |
|   10 | `sas_formats.py`               | Generates SAS format and label files that map label variable IDs, such as `v000001`, to readable label names.                                                                                          | Label/index files, especially `index_top_labels.txt`                      | `sas/word_labels_format.sas`; `sas/word_labels_full_format.sas`; other SAS helper format files |
|   11 | SAS workflow                   | Runs the external SAS Lexical/Visual Multi-dimensional Analysis workflow.                                                                                                                              | `sas/counts.txt`; SAS format files                                        | SAS factor-score, loading, ANOVA, and parameter outputs                                        |
|   12 | `factor_lists.py`              | Reads SAS factor outputs and creates readable positive and negative loading lists for each factor.                                                                                                     | SAS factor loading outputs                                                | `factors/`                                                                                     |
|   13 | `corpus_size.py`               | Calculates corpus-size summaries for reporting and for checking corpus balance.                                                                                                                        | Corpus files and/or metadata                                              | `corpus_size/corpus_size.tsv`                                                                  |
|   14 | `examples.py`                  | Selects representative high-scoring images/text entries by factor pole and writes LaTeX example extracts.                                                                                              | Factor scores; factor loading lists; corpus/image metadata                | `examples/`                                                                                    |
|   15 | `score_details.py`             | Produces a sanity-check report showing, for each item and factor, which positive- and negative-pole loading labels are present.                                                                        | Factor loading lists; label data; factor scores                           | `examples/score_details.txt`                                                                   |
|   16 | `examples_txt.py`              | Generates plain-text versions of selected examples, including score metadata and loading labels. These are useful for manual review and interpretation.                                                | Selected examples; factor scores; loading labels                          | `examples_txt/`                                                                                |

## Pipeline Overview

The pipeline can be understood as five broad stages:

| Stage                     | Description                                                                                                                    | Programmes                                                                                |
|---------------------------|--------------------------------------------------------------------------------------------------------------------------------|-------------------------------------------------------------------------------------------|
| Image corpus preparation  | Identify and separate near-duplicate images so that the analysis uses a deduplicated image corpus.                             | `find_near_duplicates.py`                                                                 |
| Vision label detection    | Use Google Cloud Vision to detect labels for each image, then retry empty or failed outputs where needed.                      | `detect_labels.py`; retry mode; notebook cleanup                                          |
| Label matrix construction | Extract label types, select top labels, build binary image-label columns, and merge them into the SAS counts matrix.           | `label_types.py`, `top_labels.py`, `columns.py`, `merge_columns.py`, `sas_formats.py`     |
| SAS-based MDA             | Run the external SAS workflow to generate factor outputs and statistical results.                                              | SAS workflow                                                                              |
| Post-SAS reporting        | Convert SAS outputs into readable factor lists, corpus summaries, example extracts, score-detail reports, and plaintext files. | `factor_lists.py`, `corpus_size.py`, `examples.py`, `score_details.py`, `examples_txt.py` |

## Notes

- The pipeline should be run from the Phase 2 project directory:

  ```text
  cl_st1_ph2_tatiana/
  ```

- `detect_labels.py` requires Google Cloud Vision credentials. By default, the project expects these to be configured in:

  ```text
  env/.env
  ```

- The main Vision labelling output is raw JSON, one file per image, under:

  ```text
  corpus/02_labelled/
  ```

- Empty label outputs were retried using `detect_labels.py` retry functionality. Persistently empty outputs were removed from the statistical analysis using the project notebook.

- The SAS step is external and must be completed before the post-SAS programmes can produce factor lists, examples, score-detail reports, and related reporting materials.

- Before regenerating binary columns, remove old column folders:

  ```shell
  rm -rf columns columns_clean
  ```

- The current Phase 2 reporting pipeline includes factor lists, corpus-size summaries, LaTeX examples, score details, and plaintext examples. Boxplot, ANOVA-table, and GPT interpretation steps are not part of the current documented run unless added later.