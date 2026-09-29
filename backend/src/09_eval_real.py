"""
09_eval_real.py: Independent Real-World Benchmark Evaluation.

Evaluates trained models against human-verified independent ground truth incidents.

Usage:
  # Evaluate Full Contextual Model:
  python src/09_eval_real.py --input data/real_test/real_expanded.csv --model data/interim/model/xgb_model_leakfree.json

  # Evaluate Pure Radiometric Ablation Model:
  python src/09_eval_real.py --input data/real_test/real_expanded.csv --model data/interim/model/xgb_model_ablation.json --no-landcover --no-persistence
"""

import argparse
import json
from pathlib import Path
import pandas as pd
import numpy as np
import xgboost as xgb
from sklearn.metrics import classification_report, confusion_matrix

from common import *


def evaluate_on_real_incidents(
    input_csv_path: Path,
    model_path: Path,
    include_landcover: bool = True,
    include_persistence: bool = True,
):
    print("\n" + "=" * 75)
    print(f"EVALUATING MODEL: {model_path.name}")
    print(f"ON TEST SET:     {input_csv_path.name}")
    print(f"CONFIG:          LandCover={include_landcover} | Persistence={include_persistence}")
    print("=" * 75)

    if not input_csv_path.exists():
        raise FileNotFoundError(f"Missing test file: {input_csv_path}")
    if not model_path.exists():
        raise FileNotFoundError(f"Missing model file: {model_path}")

    real_df = pd.read_csv(input_csv_path)
    print(f"Loaded {len(real_df)} independent human-verified benchmark incidents.")

    model = xgb.XGBClassifier()
    model.load_model(str(model_path))

    X_real, feature_cols = prep_features(
        real_df,
        include_landcover=include_landcover,
        include_persistence=include_persistence,
    )
    y_true = label_codes(real_df["label"])
    y_pred = model.predict(X_real)
    probs = model.predict_proba(X_real)

    correct_count = 0
    print("\nIndividual Event Predictions:")
    print("-" * 75)
    for i, row in real_df.iterrows():
        pred_idx = y_pred[i]
        pred_label = LABELS[pred_idx]
        actual = row["label"]
        prob = probs[i][pred_idx]
        is_match = (pred_label == actual)
        if is_match:
            correct_count += 1
        match_str = "MATCH" if is_match else f"MISMATCH -> Got {pred_label}"
        print(f"[{i+1:02d}] {row['source_note'][:55]:<55} | Actual: {actual:<20} | Pred: {pred_label:<20} ({prob*100:5.1f}%) [{match_str}]")

    print("\n" + "=" * 75)
    print(f"BENCHMARK CLASSIFICATION REPORT ({correct_count}/{len(real_df)} = {correct_count/len(real_df)*100:.1f}% Accuracy)")
    print("=" * 75)
    rep = classification_report(
        y_true, y_pred,
        labels=range(len(LABELS)),
        target_names=LABELS,
        zero_division=0
    )
    print(rep)

    cm = confusion_matrix(y_true, y_pred, labels=range(len(LABELS)))
    cm_df = pd.DataFrame(cm, index=LABELS, columns=LABELS)
    print("Confusion Matrix:")
    print(cm_df)

    out_report_name = f"benchmark_{model_path.stem}_{input_csv_path.stem}.txt"
    report_path = MODELS / out_report_name
    with open(report_path, "w") as f:
        f.write(f"IFDCS Benchmark Evaluation Report: {model_path.name}\n")
        f.write(f"Test Set: {input_csv_path.name} ({len(real_df)} events)\n")
        f.write("=" * 65 + "\n\n")
        f.write(f"Overall Accuracy: {correct_count}/{len(real_df)} ({correct_count/len(real_df)*100:.1f}%)\n\n")
        f.write("Classification Report:\n")
        f.write(rep + "\n\n")
        f.write("Confusion Matrix:\n")
        f.write(cm_df.to_string() + "\n\n")
        f.write("Detailed Event Log:\n")
        for i, row in real_df.iterrows():
            pred_label = LABELS[y_pred[i]]
            f.write(f"- {row['source_note']}: Actual={row['label']}, Pred={pred_label} ({probs[i][y_pred[i]]*100:.1f}%)\n")

    print(f"\nSaved benchmark evaluation report to: {report_path.name}")
    return rep, cm_df


def main():
    parser = argparse.ArgumentParser(description="Evaluate on Real Benchmark Incidents")
    parser.add_argument("--input", type=str, default=str(REAL_TEST / "real_expanded.csv"), help="Input real incidents CSV")
    parser.add_argument("--model", type=str, default=str(MODELS / "xgb_model_production.json"), help="Path to trained XGBoost model")
    parser.add_argument("--no-landcover", action="store_true", help="Set if evaluating ablation model without land cover")
    parser.add_argument("--no-persistence", action="store_true", help="Set if evaluating ablation model without persistence")
    args = parser.parse_args()

    input_path = Path(args.input)
    model_path = Path(args.model)

    evaluate_on_real_incidents(
        input_csv_path=input_path,
        model_path=model_path,
        include_landcover=not args.no_landcover,
        include_persistence=not args.no_persistence,
    )


if __name__ == "__main__":
    main()
