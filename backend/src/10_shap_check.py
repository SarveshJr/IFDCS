"""
10_shap_check.py: SHAP Feature Importance & Circularity Risk Audit.

Usage:
  python src/10_shap_check.py --check-circularity
"""

import argparse
import json
from pathlib import Path
import numpy as np
import pandas as pd
import xgboost as xgb
import shap

from common import *


def check_circularity(model, X_sample, feature_cols):
    """
    Quantify how much the model leans on borderline contextual features
    (land cover, persistence) vs pure physical radiometry (FRP, temperatures, deltas).
    """
    print("\n" + "=" * 70)
    print("SHAP CIRCULARITY & FEATURE RELIANCE AUDIT")
    print("=" * 70)

    explainer = shap.TreeExplainer(model)
    shap_values = explainer.shap_values(X_sample)

    if isinstance(shap_values, list):
        mean_abs_shap = np.mean([np.abs(sv).mean(axis=0) for sv in shap_values], axis=0)
    elif len(shap_values.shape) == 3:
        mean_abs_shap = np.mean(np.abs(shap_values), axis=(0, 2))
    else:
        mean_abs_shap = np.mean(np.abs(shap_values), axis=0)

    importance_df = pd.DataFrame({
        "Feature": feature_cols,
        "Mean_SHAP_Impact": mean_abs_shap
    }).sort_values(by="Mean_SHAP_Impact", ascending=False)

    total_importance = importance_df["Mean_SHAP_Impact"].sum()
    importance_df["Share_%"] = (importance_df["Mean_SHAP_Impact"] / total_importance) * 100.0

    print("\nFeature Impact Breakdown:")
    print(importance_df.to_string(index=False))

    # Group into categories
    lc_cols = [c for c in feature_cols if c.startswith("lc_")]
    per_cols = [c for c in feature_cols if "persistence" in c]
    rad_cols = [c for c in feature_cols if c in RADIOMETRIC_FEATURES]

    lc_share = importance_df[importance_df["Feature"].isin(lc_cols)]["Share_%"].sum()
    per_share = importance_df[importance_df["Feature"].isin(per_cols)]["Share_%"].sum()
    rad_share = importance_df[importance_df["Feature"].isin(rad_cols)]["Share_%"].sum()

    print("\n" + "-" * 50)
    print("FEATURE CATEGORY RELIANCE:")
    print(f"  • Land Cover Features:         {lc_share:.1f}%")
    print(f"  • Persistence Features:        {per_share:.1f}%")
    print(f"  • Pure Radiometry & Physics:   {rad_share:.1f}%")
    print("-" * 50)

    if (lc_share + per_share) > 75.0:
        print("\n[CRITICAL DIAGNOSIS]")
        print("  WARNING: High circularity risk! >75% of model decisions are driven by")
        print("  land cover and persistence thresholds rather than satellite thermal radiometry.")
        print("  Run ablation study: python src/08_split_train_eval.py --no-landcover --no-persistence --tag ablation")
    else:
        print("\n[HEALTHY BALANCE]")
        print("  Model exhibits balanced reliance across thermal radiometry and spatial context.")

    return importance_df


def main():
    parser = argparse.ArgumentParser(description="SHAP Circularity and Feature Audit")
    parser.add_argument("--check-circularity", action="store_true", help="Perform circularity audit")
    parser.add_argument("--model", type=str, default=str(MODELS / "xgb_model_production.json"), help="Model file path")
    parser.add_argument("--no-landcover", action="store_true", help="Ablation: exclude land cover")
    parser.add_argument("--no-persistence", action="store_true", help="Ablation: exclude persistence")
    args = parser.parse_args()

    model_path = Path(args.model)
    if not model_path.exists():
        raise FileNotFoundError(f"Missing {model_path.name}. Run training first.")

    model = xgb.XGBClassifier()
    model.load_model(str(model_path))

    df = pd.read_csv(INTERIM / "firms_labeled_augmented.csv")
    df = df[df["label"].isin(LABELS)].sample(n=min(2500, len(df)), random_state=42)

    X_sample, feature_cols = prep_features(
        df,
        include_landcover=not args.no_landcover,
        include_persistence=not args.no_persistence,
    )

    if args.check_circularity or True:
        imp_df = check_circularity(model, X_sample, feature_cols)
        
        # Save audit report
        audit_file = MODELS / f"shap_circularity_audit_{model_path.stem}.json"
        audit_dict = dict(zip(imp_df["Feature"], imp_df["Share_%"]))
        with open(audit_file, "w") as f:
            json.dump(audit_dict, f, indent=2)
        print(f"\nSaved audit results to: {audit_file.name}")


if __name__ == "__main__":
    main()
