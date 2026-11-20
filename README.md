# CHIP 705 Final Project

## Working title

**Can Electrophysiological Features Distinguish Spiny and Aspiny Mouse Neurons? A Machine Learning Analysis of the Allen Cell Types Database**

## Research question

Can precomputed electrophysiological features distinguish mouse neurons annotated as **spiny** from those annotated as **aspiny** in the Allen Cell Types Database?

## Scope

- Use public, cell-level data from the Allen Cell Types Database.
- Restrict the analysis to mouse cells with a spiny or aspiny annotation.
- Use electrophysiology measurements as model inputs; do not use morphology measurements, cell labels, or metadata such as Cre line as predictors.
- Compare Logistic Regression and Random Forest as baseline classifiers.
- Report class counts, missingness, group comparisons, and test-set classification metrics.
- Treat this as an exploratory classification study. Model performance does not establish a biological cause or clinical utility.

## Planned workflow

1. Retrieve the public Allen metadata and computed electrophysiology features.
2. Inspect the data and document inclusion/exclusion counts and missing values.
3. Select a small, interpretable set of electrophysiology features and create descriptive plots.
4. Split data with stratification; keep preprocessing inside the training pipeline to avoid leakage. If the sample supports it, add a sensitivity analysis that holds out mouse lines.
5. Compare the two classifiers using balanced accuracy, precision, recall, F1, and a confusion matrix. Report the class distribution alongside accuracy.
6. Write the report in the requested format, then adapt its key figures and conclusions for the SDIS poster and 5-minute talk.

## Current progress

- The Allen API data have been retrieved and joined successfully.
- The primary cohort contains 1,813 mouse cells: 921 aspiny and 892 spiny. The 107 `sparsely spiny` cells are excluded from the binary analysis.
- Initial descriptive figures and data-quality summaries are in `figures/` and `results/`.
- Initial model comparison is complete using 5-fold `StratifiedGroupKFold` grouped by mouse line. The pooled out-of-fold Random Forest accuracy is 0.921 and ROC-AUC is 0.977; Logistic Regression accuracy is 0.861 and ROC-AUC is 0.935. These are preliminary results and must be interpreted as classification performance on held-out mouse lines, not as causal or clinical evidence.

## Repository

GitHub repository: https://github.com/canoki1717/CHIP705-FinalProject

## Run locally

After creating and activating a Python virtual environment and installing `requirements.txt`, run:

```bash
python 01_download_data.py
python 02_explore_data.py
python 03_model_and_evaluate.py
```

The `.gitignore` excludes the virtual environment, downloaded source tables, the derived cell-level analysis table, and cell-level out-of-fold predictions. Aggregate result tables and figures are included. The scripts regenerate the excluded files from the public Allen API.

## Project files

- `01_download_data.py`: retrieves the source tables and saves raw and merged CSV files under `data/`.
- `requirements.txt`: Python packages needed for the data workflow.
- `data/README.md`: data provenance and file notes.
- `report/`: project report draft.
- `figures/`: analysis figures will be saved here.

## Data source

Allen Institute for Brain Science, Allen Cell Types Database. The database provides single-cell electrophysiology features and cell metadata, including dendrite type. See the Allen API documentation and the project's data notes for citations and access details.

## Reproducibility

The download script records the retrieval date and source endpoint in `data/README.md`. The raw source tables are not committed; the download script retrieves them from the public API.
