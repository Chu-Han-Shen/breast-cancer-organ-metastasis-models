# MetMap Distilled Models

This directory contains locked random-forest models for evaluating transferable liver- and bone-metastasis risk scores in MetMap breast cancer cell lines.

## Directory structure

```text
data/                 Processed MetMap model inputs and metastatic phenotypes
models/               Locked liver and bone random-forest deployment bundles
features/             Feature order, retention status, and imputation values
scripts/              Prediction, validation, and figure-generation script
expected_results/     Reference predictions and statistical results
figures/              Reference correlation forest plots
results/              Results generated when the script is executed
```

## Model bundles

Each model bundle contains:

- the locked `ranger` regression model;
- the required feature names and order;
- training-derived missing-value imputation values;
- the risk-score transformation rule.

The predicted rank-based z score is transformed into a risk score between 0 and 1 using:

```r
risk_score <- pnorm(predicted_rank_z)
```

## Run the analysis

From the repository root, run:

```bash
Rscript run_MetMap.R
```

Alternatively, from this directory run:

```r
source("scripts/run_MetMap_prediction_and_plot.R")
```

## Reproducibility checks

The script compares the newly generated liver and bone risk scores with the reference predictions in `expected_results/`.

Successful execution reports:

```text
Liver prediction reproduced: TRUE
Bone prediction reproduced: TRUE
```

## Input variables

Only variables listed in each model bundle's `retained_features` field are passed to the model. The metastatic phenotype columns `mean.liver` and `mean.bone` are used only for validation and are not model inputs.
