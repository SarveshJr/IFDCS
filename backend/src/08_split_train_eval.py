"""
08_split_train_eval.py: Spatial Block Cross-Validation & Ablation Training Pipeline.

Usage:
  # Full contextual model (10m LULC + Persistence + Thermal Radiometry):
  python src/08_split_train_eval.py

  # Pure Radiometric Physics Model (Ablation Test - NO Land Cover, NO Persistence):
  python src/08_split_train_eval.py --no-landcover --no-persistence --tag ablation
"""

import argparse
import json
from pathlib import Path
import numpy as np
import pandas as pd
import xgboost as xgb
from sklearn.model_selection import GroupKFold
from sklearn.metrics import classification_report, confusion_matrix

from common import *


def train_and_eval_spatial(
    include_landcover: bool = True,
    include_persistence: bool = True,
    tag: str = "full",
):
    print("\n" + "=" * 70)
    print(f"EXPERIMENT [{tag.upper()}]: Spatial Block Cross-Validation")
    print(f"  • Include Land Cover:   {include_landcover}")
    print(f"  • Include Persistence:  {include_persistence}")
    print("=" * 70)

    input_file = INTERIM / "firms_labeled_augmented.csv"
    if not input_file.exists():
        input_file = INTERIM / "firms_labeled.csv"

    df_raw = pd.read_csv(input_file)
    df = df_raw[df_raw["label"].isin(LABELS)].copy()

    # Spatial 0.25-degree grid block clustering for zero geographic leakage
    df["spatial_block"] = (df["latitude"] // 0.25).astype(str) + "_" + (df["longitude"] // 0.25).astype(str)
    print(f"Loaded {len(df):,} events across {df['spatial_block'].nunique():,} isolated spatial blocks.")

    X, feat_cols = prep_features(
        df,
        include_landcover=include_landcover,
        include_persistence=include_persistence,
    )
    y = label_codes(df["label"])
    groups = df["spatial_block"]

    print(f"\nFeature matrix X shape: {X.shape} ({len(feat_cols)} features)")
    print(f"Features in this model:\n{feat_cols}")

    # Balanced square-root class weighting
    class_counts = y.value_counts()
    n_classes = len(LABELS)
    total = len(y)
    class_weights = {c: np.sqrt(total / (n_classes * max(count, 1))) for c, count in class_counts.items()}
    sw = y.map(class_weights)

    gkf = GroupKFold(n_splits=5)
    oof_preds = np.zeros(len(df), dtype=int)

    for fold, (tr, te) in enumerate(gkf.split(X, y, groups), 1):
        model = xgb.XGBClassifier(
            n_estimators=200, max_depth=5, learning_rate=0.08,
            min_child_weight=4, subsample=0.8, colsample_bytree=0.8,
            reg_lambda=2.0, objective="multi:softprob", num_class=len(LABELS),
            random_state=42 + fold
        )
        model.fit(X.iloc[tr], y.iloc[tr], sample_weight=sw.iloc[tr])
        oof_preds[te] = model.predict(X.iloc[te])

    print("\n" + "=" * 70)
    print(f"5-FOLD SPATIAL BLOCK CV RESULTS [{tag.upper()}]")
    print("=" * 70)
    rep = classification_report(y, oof_preds, labels=range(len(LABELS)), target_names=LABELS, zero_division=0)
    print(rep)

    cm = confusion_matrix(y, oof_preds, labels=range(len(LABELS)))
    cm_df = pd.DataFrame(cm, index=LABELS, columns=LABELS)
    print("Spatial Block Confusion Matrix:")
    print(cm_df)

    # Train final deployment model on all data
    print(f"\nTraining final [{tag}] model on all data...")
    final_model = xgb.XGBClassifier(
        n_estimators=250, max_depth=5, learning_rate=0.08,
        min_child_weight=4, subsample=0.8, colsample_bytree=0.8,
        reg_lambda=2.0, objective="multi:softprob", num_class=len(LABELS),
        random_state=42
    )
    final_model.fit(X, y, sample_weight=sw)

    model_filename = f"xgb_model_{tag}.json"
    final_model.save_model(str(MODELS / model_filename))
    print(f"Saved [{tag}] model to: {model_filename}")

    # Save evaluation report
    report_filename = f"{tag}_evaluation_report.txt"
    report_file = MODELS / report_filename
    with open(report_file, "w") as f:
        f.write(f"IFDCS Spatial Block Cross-Validation Report [{tag.upper()}]\n")
        f.write("=" * 65 + "\n\n")
        f.write(f"Model Configuration: Tag={tag}\n")
        f.write(f"Land Cover Included: {include_landcover}\n")
        f.write(f"Persistence Included: {include_persistence}\n")
        f.write(f"Features: {feat_cols}\n\n")
        f.write("Out-of-Fold Classification Report (Zero Spatial Leakage):\n")
        f.write(rep + "\n\n")
        f.write("Confusion Matrix:\n")
        f.write(cm_df.to_string() + "\n")

    print(f"Report saved to: {report_file.name}")
    return final_model, rep, cm_df


def main():
    parser = argparse.ArgumentParser(description="Spatial Block Cross-Validation & Ablation")
    parser.add_argument("--no-landcover", action="store_true", help="Exclude land cover features")
    parser.add_argument("--no-persistence", action="store_true", help="Exclude persistence features")
    parser.add_argument("--tag", type=str, default="leakfree", help="Model tag (e.g. leakfree, ablation)")
    args = parser.parse_args()

    include_landcover = not args.no_landcover
    include_persistence = not args.no_persistence

    train_and_eval_spatial(
        include_landcover=include_landcover,
        include_persistence=include_persistence,
        tag=args.tag,
    )


if __name__ == "__main__":
    main()
