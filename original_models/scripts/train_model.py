#!/usr/bin/env python3
"""
Train a TabPFN/AutoTabPFNClassifier-based organ-specific metastasis model.

This script follows the original modeling workflow:
- reads a preprocessed numeric input matrix
- removes the sample ID and target columns from model inputs
- performs a stratified train/internal-test split
- trains AutoTabPFNClassifier
- outputs AUC and ROC coordinates
- optionally outputs threshold-dependent metrics if --threshold is provided

No automatic median imputation is performed. Input matrices should be preprocessed before use.
"""

import argparse
import json
from pathlib import Path

import joblib
import pandas as pd
from sklearn.metrics import (
    accuracy_score,
    precision_recall_fscore_support,
    roc_auc_score,
    roc_curve,
)
from sklearn.model_selection import train_test_split

from tabpfn_extensions.post_hoc_ensembles.sklearn_interface import AutoTabPFNClassifier


def parse_args():
    parser = argparse.ArgumentParser(description="Train an organ-specific metastasis prediction model.")
    parser.add_argument("--input", required=True, help="Input CSV file.")
    parser.add_argument("--target", required=True, help="Binary target column, e.g. Bone_metastasis or Liver_metastasis.")
    parser.add_argument("--id-col", default="Tumor_Sample_Barcode", help="Sample ID column.")
    parser.add_argument("--output-model", required=True, help="Path to save the trained model bundle.")
    parser.add_argument("--output-metrics", required=True, help="Path to save internal test-set metrics.")
    parser.add_argument("--output-roc", required=True, help="Path to save ROC coordinates.")
    parser.add_argument("--threshold", type=float, default=None, help="Optional probability threshold for binary classification.")
    parser.add_argument("--test-size", type=float, default=0.30, help="Internal test-set fraction.")
    parser.add_argument("--random-state", type=int, default=42, help="Random seed.")
    parser.add_argument("--device", default="cuda", choices=["cuda", "cpu"], help="Device for AutoTabPFNClassifier.")
    parser.add_argument("--n-ensemble-configurations", type=int, default=32, help="Number of ensemble configurations.")
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

    if args.target not in df.columns:
        raise ValueError(f"Target column '{args.target}' was not found in input file.")

    drop_cols = [args.target]
    if args.id_col in df.columns:
        drop_cols.append(args.id_col)

    feature_cols = [col for col in df.columns if col not in drop_cols]
    if len(feature_cols) == 0:
        raise ValueError("No model-input feature columns were found.")

    x_df = df[feature_cols].apply(pd.to_numeric, errors="coerce")
    check_missing_values(x_df)

    y = df[args.target].astype(int).values

    x_train, x_test, y_train, y_test = train_test_split(
        x_df.values,
        y,
        test_size=args.test_size,
        stratify=y,
        random_state=args.random_state,
    )

    clf = AutoTabPFNClassifier(device=args.device)
    clf.N_ensemble_configurations = args.n_ensemble_configurations
    clf.fit(x_train, y_train)

    pred_prob = clf.predict_proba(x_test)[:, 1]
    auc = roc_auc_score(y_test, pred_prob)

    metrics = {
        "target": args.target,
        "n_samples": len(df),
        "n_train": len(y_train),
        "n_internal_test": len(y_test),
        "auc": auc,
        "random_state": args.random_state,
        "test_size": args.test_size,
        "n_ensemble_configurations": args.n_ensemble_configurations,
        "threshold": args.threshold if args.threshold is not None else "not_provided",
    }

    if args.threshold is not None:
        pred_label = (pred_prob >= args.threshold).astype(int)
        acc = accuracy_score(y_test, pred_label)
        precision, recall, f1, _ = precision_recall_fscore_support(
            y_test, pred_label, average="binary", zero_division=0
        )
        metrics.update(
            {
                "accuracy": acc,
                "precision": precision,
                "recall": recall,
                "f1": f1,
            }
        )

    fpr, tpr, roc_thresholds = roc_curve(y_test, pred_prob)
    roc_df = pd.DataFrame(
        {
            "fpr": fpr,
            "sensitivity": tpr,
            "specificity": 1 - fpr,
            "threshold": roc_thresholds,
        }
    )

    metrics_df = pd.DataFrame([metrics])

    Path(args.output_model).parent.mkdir(parents=True, exist_ok=True)
    Path(args.output_metrics).parent.mkdir(parents=True, exist_ok=True)
    Path(args.output_roc).parent.mkdir(parents=True, exist_ok=True)

    model_bundle = {
        "model": clf,
        "feature_cols": feature_cols,
        "target": args.target,
        "id_col": args.id_col,
        "threshold": args.threshold,
        "random_state": args.random_state,
        "test_size": args.test_size,
        "preprocessing": "No automatic imputation was performed. Input feature matrix must be preprocessed and numeric.",
    }

    joblib.dump(model_bundle, args.output_model)
    metrics_df.to_csv(args.output_metrics, index=False)
    roc_df.to_csv(args.output_roc, index=False)

    print(json.dumps(metrics, indent=2))


if __name__ == "__main__":
    main()
