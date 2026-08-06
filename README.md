# Breast Cancer Organ-Specific Metastasis Models

This repository contains code and model resources for organ-specific metastasis prediction in breast cancer.

## Repository contents

### Original models

The `original_models/` directory contains the original AutoTabPFN-based modeling workflow, including:

- model-training code;
- external-cohort prediction code;
- ROC plotting code;
- example liver- and bone-model input files.

The original patient-level training data and trained AutoTabPFN model objects are not distributed because the genomic data are controlled.

### Distilled models

The `distilled_models/MetMap/` directory contains locked random-forest models distilled from the original organ-specific metastasis models.

This module provides:

- processed MetMap model inputs and metastatic phenotypes;
- locked liver- and bone-metastasis random-forest model bundles;
- model feature manifests and training-derived imputation values;
- scripts for generating cell-line-level risk scores;
- scripts and expected results for reproducing the MetMap correlation analysis and figure.

## Quick start

The MetMap analysis requires R and the following packages:

```r
install.packages(c("readr", "dplyr", "tibble", "ranger", "ggplot2"))
```

From the repository root, run:

```bash
Rscript run_MetMap.R
```

The script generates:

```text
distilled_models/MetMap/results/MetMap_risk_scores.csv
distilled_models/MetMap/results/MetMap_correlation_results.csv
distilled_models/MetMap/figures/MetMap_liver_bone_correlation_forest.pdf
distilled_models/MetMap/figures/MetMap_liver_bone_correlation_forest.png
```

## Reproducibility scope

The original AutoTabPFN module provides code-level reproducibility using example inputs.

The distilled MetMap module provides inference-level reproducibility using locked deployment models, public input data, expected predictions, and figure-generation code.

## Data availability

Patient-level genomic training data are controlled and are not included in this repository. Processed MetMap inputs required for the external validation analysis are provided.

## License

See the `LICENSE` file for details.
