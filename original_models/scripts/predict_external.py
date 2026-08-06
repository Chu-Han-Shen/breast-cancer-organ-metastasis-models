#!/usr/bin/env python3
"""
Apply a trained TabPFN/AutoTabPFNClassifier-based metastasis model to an external cohort.

The script outputs predicted probabilities. If the model bundle contains a threshold,
it also outputs high-/low-risk group assignments.

No automatic median imputation is performed. Input matrices should be preprocessed before use.
"""

import argparse
from pathlib import Path

import joblib
import numpy as np
import pandas as pd


def parse_args():
    parser = argparse.ArgumentParser(description="Apply a trained metastasis prediction model.")
    parser.add_argument("--input", required=True, help="External input CSV file.")
    parser.add_argument("--model", required=True, help="Trained model bundle saved by train_model.py.")
    parser.add_argument("--output", required=True, help="Output CSV file with predicted probabilities.")
    return parser.parse_args()


def check_missing_values(x_df):
    missing_counts = x_df.isna().sum()
    missing_counts = missing_counts[missing_counts > 0]
    if len(missing_counts) > 0:
        message = (
            "Missing values were detected in model-input columns. "
            "This script does not perform automatic imputation. "
            "Please provide a complete preprocessed input matrix. "
            "Columns with missing values: "
            + ", ".join([f"{col}={n}" for col, n in missing_counts.items()])
        )
        raise ValueError(message)


def main():
    args = parse_args()

    df = pd.read_csv(args.input)
    bundle = joblib.load(args.model)

    model = bundle["model"]
    feature_cols = bundle["feature_cols"]
    threshold = bundle.get("threshold", None)

    missing_cols = [col for col in feature_cols if col not in df.columns]
    if missing_cols:
        raise ValueError(
            "The external input file is missing required feature columns: "
            + ", ".join(missing_cols)
        )

    x_df = df[feature_cols].apply(pd.to_numeric, errors="coerce")
    check_missing_values(x_df)

    pred_prob = model.predict_proba(x_df.values)[:, 1]

    output_df = df.copy()
    output_df["Metastasis_Probability"] = pred_prob

    if threshold is not None:
        output_df["Risk_Group"] = np.where(pred_prob >= threshold, "High_risk", "Low_risk")

    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    output_df.to_csv(args.output, index=False, encoding="utf-8-sig")

    print(f"Saved prediction results to {args.output}")


if __name__ == "__main__":
    main()
