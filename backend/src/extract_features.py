"""
Step 2: Basic temporal and astronomical features extraction.

Reads:
  data/interim/firms_india_2025.csv
Writes:
  data/interim/firms_india_2025_features.csv
"""

from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent.parent
INTERIM_DIR = ROOT / "DATA" / "interim"
INPUT_CSV = INTERIM_DIR / "firms_india_2025.csv"
OUTPUT_CSV = INTERIM_DIR / "firms_india_2025_features.csv"


def extract_features(df: pd.DataFrame) -> pd.DataFrame:
    print(f"Loaded {len(df)} records. Calculating features...")
    # Extract UTC hour and approx IST hour (+5.5h or approx +5)
    df["hour_utc"] = df["acq_time"] // 100
    df["minute_utc"] = df["acq_time"] % 100
    df["hour"] = (df["hour_utc"] + 5) % 24  # approx IST hour
    
    # Month
    dt = pd.to_datetime(df["acq_date"])
    df["month"] = dt.dt.month
    df["day_of_year"] = dt.dt.dayofyear
    
    # Day/Night flag
    df["is_night"] = (df["daynight"] == "N").astype(int)
    
    print("Feature summary:")
    print(" - Month distribution:\n", df["month"].value_counts().sort_index())
    print(" - Day vs Night counts:\n", df["is_night"].value_counts())
    return df


def main():
    if not INPUT_CSV.exists():
        raise SystemExit(f"Input file not found: {INPUT_CSV}. Please run Step 1 first.")
    
    df = pd.read_csv(INPUT_CSV)
    df = extract_features(df)
    df.to_csv(OUTPUT_CSV, index=False)
    print(f"\nSaved enriched data to: {OUTPUT_CSV.name}")


if __name__ == "__main__":
    main()
