# Organ-specific metastasis prediction model

This repository contains scripts for training and applying TabPFN/AutoTabPFNClassifier-based organ-specific metastasis prediction models in breast cancer.

The scripts accompany the manuscript:

**Pre-existing biological programs in primary breast cancer dictate organ-specific metastasis: A real-world, multi-omics study**

## Overview

This repository provides scripts for:

1. Training TabPFN/AutoTabPFNClassifier-based models for organ-specific metastasis prediction.
2. Evaluating model performance in an internal test set.
3. Applying trained models to an independent cohort.
4. Generating ROC curve visualizations.

The main models described in the manuscript include:

- Bone metastasis prediction model
- Liver metastasis prediction model

## Repository structure

```text
organ_metastasis_model/
├── README.md
├── requirements.txt
├── LICENSE
├── data/
│   ├── example_bone_input.csv
│   └── example_liver_input.csv
├── models/
│   └── README.md
├── results/
│   └── README.md
└── scripts/
    ├── train_model.py
    ├── predict_external.py
    └── plot_roc_curve.R
```

## Requirements

The Python scripts were written for Python 3.x and require:

- pandas
- numpy
- scikit-learn
- joblib
- tabpfn
- tabpfn-extensions

The R visualization script was written for R 4.3.2 and requires:

- ggplot2
- dplyr
- readr

No non-standard hardware is required for running the example scripts. GPU acceleration can be used for TabPFN if available.

## Installation

Clone the repository and install dependencies:

```bash
git clone https://github.com/Chu-Han-Shen/organ_metastasis_model.git
cd organ_metastasis_model

pip install -r requirements.txt
```

For R visualization, install the required R packages:

```r
install.packages(c("ggplot2", "dplyr", "readr"))
```

Typical installation time is approximately 10-30 minutes on a standard desktop computer, depending on internet speed and package availability.

## Input data format

Input files should be CSV files with one row per patient.

Required columns for training:

- `Tumor_Sample_Barcode`: patient/sample identifier
- `Bone_metastasis` or `Liver_metastasis`: binary outcome label for model training and internal evaluation
- clinical, laboratory and genomic feature columns used as model inputs

Required columns for external prediction:

- `Tumor_Sample_Barcode`: patient/sample identifier
- the same feature columns used during model training
- the outcome label is optional for prediction

Example input files are provided in the `data/` folder to illustrate the required format.

## Data preprocessing

These scripts intentionally do not perform median imputation or other automated missing-value imputation, in order to match the original analysis workflow more closely. Input files should therefore be preprocessed before model training or prediction. If missing values are present in model-input columns, the script will stop and ask the user to provide a complete preprocessed input matrix.

All categorical variables should be encoded numerically before use.

## Threshold and risk-group assignment

The model outputs sample-level predicted probabilities. A probability threshold for assigning high- and low-risk groups is not hard-coded in this repository.

If a user provides `--threshold`, the scripts additionally output binary predicted labels or high-/low-risk groups. If no threshold is provided, only predicted probabilities and threshold-free performance metrics, such as AUC and ROC coordinates, are generated.

This design avoids hard-coding manuscript-specific cutoffs in the public code.

## Usage

### Train a liver metastasis model

```bash
python scripts/train_model.py \
  --input data/example_liver_input.csv \
  --target Liver_metastasis \
  --id-col Tumor_Sample_Barcode \
  --output-model models/model_liver.joblib \
  --output-metrics results/liver_internal_metrics.csv \
  --output-roc results/liver_internal_roc.csv \
  --test-size 0.30 \
  --random-state 42
```

### Train a bone metastasis model

```bash
python scripts/train_model.py \
  --input data/example_bone_input.csv \
  --target Bone_metastasis \
  --id-col Tumor_Sample_Barcode \
  --output-model models/model_bone.joblib \
  --output-metrics results/bone_internal_metrics.csv \
  --output-roc results/bone_internal_roc.csv \
  --test-size 0.30 \
  --random-state 42
```

### Optional: train with a user-defined threshold

```bash
python scripts/train_model.py \
  --input data/example_liver_input.csv \
  --target Liver_metastasis \
  --id-col Tumor_Sample_Barcode \
  --output-model models/model_liver.joblib \
  --output-metrics results/liver_internal_metrics.csv \
  --output-roc results/liver_internal_roc.csv \
  --threshold <user_defined_threshold>
```

### Apply a trained model to an external cohort

```bash
python scripts/predict_external.py \
  --input data/example_liver_input.csv \
  --model models/model_liver.joblib \
  --output results/liver_external_prediction.csv
```

If the trained model bundle contains a threshold, the output will also include a `Risk_Group` column. Otherwise, the output will include predicted probabilities only.

### Plot ROC curve

```bash
Rscript scripts/plot_roc_curve.R \
  results/liver_internal_roc.csv \
  results/liver_internal_roc.pdf \
  "#F6B956" \
  "Liver metastasis ROC"
```

```bash
Rscript scripts/plot_roc_curve.R \
  results/bone_internal_roc.csv \
  results/bone_internal_roc.pdf \
  "#5D9BD4" \
  "Bone metastasis ROC"
```

## Expected output

The training script outputs:

- a trained model bundle saved as `.joblib`
- internal test-set performance metrics
- ROC curve coordinate file

The external prediction script outputs:

- sample-level predicted metastasis probability
- optional binary high-/low-risk group assignment if a threshold is provided

The ROC plotting script outputs:

- a PDF ROC curve

The demo scripts should run within several minutes on a standard desktop computer when using the small example datasets.

## Notes on reproducibility

The scripts are provided to document the modeling workflow used in the manuscript. Exact reproduction of all manuscript-level numerical results requires access to the original patient-level clinical-genomic datasets, which are subject to institutional and ethical data-sharing restrictions.

Patient-level FUSCC clinical-genomic data are not included in this repository because of patient privacy, ethics restrictions and institutional data-sharing policies. De-identified data may be made available upon reasonable request and approval by the relevant committees.

## License

This repository is provided under the MIT License for academic review and research use.
