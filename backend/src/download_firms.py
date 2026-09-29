"""
Step 1: download India VIIRS hotspots from NASA FIRMS.

Put this file at:  ifdcs_data/src/download_firms.py
Run from the ifdcs_data folder:  python src/download_firms.py

Output:
  data/raw/firms/firms_<date>.csv   (one file per 10-day chunk, safe to re-run)
  data/interim/firms_india_2025.csv (all chunks merged)
"""
import io
import os
import time
from pathlib import Path

import pandas as pd
import requests

# ---------- SETTINGS (edit these) ----------
MAP_KEY = os.environ.get("FIRMS_MAP_KEY", "8551cc2bf81f8958c6321637e0900067")
SOURCE = "VIIRS_SNPP_SP"        # SP = archived standard data. Use VIIRS_SNPP_NRT for the last ~3 months
BBOX = "68,6,98,38"             # India bounding box (west, south, east, north)
DAY_RANGE = 5                   # NASA FIRMS Area API limit is max 5 days per query
START = "2025-01-01"
END = "2025-12-31"
OUT_NAME = "firms_india_2025.csv"
ROOT = Path(__file__).resolve().parent.parent.parent
DATA_DIR = ROOT / "DATA"
RAW_DIR = DATA_DIR / "raw" / "firms"
INTERIM_DIR = DATA_DIR / "interim"
RAW_DIR.mkdir(parents=True, exist_ok=True)
INTERIM_DIR.mkdir(parents=True, exist_ok=True)


def fetch_chunk(start_date: str, tries: int = 3):
    """Download 5 days of data starting at start_date. Returns a DataFrame (maybe empty)."""
    url = (
        f"https://firms.modaps.eosdis.nasa.gov/api/area/csv/"
        f"{MAP_KEY}/{SOURCE}/{BBOX}/{DAY_RANGE}/{start_date}"
    )
    for attempt in range(1, tries + 1):
        try:
            resp = requests.get(url, timeout=120)
            text = resp.text.strip()
            if resp.status_code != 200 or not text.startswith("latitude"):
                # FIRMS returns plain text errors (bad key, limit reached, etc.)
                print(f"  ! unexpected reply for {start_date}: {text[:120]}")
                time.sleep(5 * attempt)
                continue
            return pd.read_csv(io.StringIO(text))
        except requests.RequestException as e:
            print(f"  ! network error ({e}), retry {attempt}/{tries}")
            time.sleep(5 * attempt)
    return None


def main():
    if MAP_KEY == "PASTE_YOUR_KEY_HERE":
        raise SystemExit("Set your MAP_KEY first (see instructions).")

    starts = pd.date_range(START, END, freq=f"{DAY_RANGE}D")
    print(f"{len(starts)} chunks to download")

    for i, d in enumerate(starts, 1):
        stamp = d.strftime("%Y-%m-%d")
        out = RAW_DIR / f"firms_{stamp}.csv"
        if out.exists():
            print(f"[{i}/{len(starts)}] {stamp} already downloaded, skipping")
            continue
        df = fetch_chunk(stamp)
        if df is None:
            print(f"[{i}/{len(starts)}] {stamp} FAILED (re-run the script later)")
            continue
        df.to_csv(out, index=False)
        print(f"[{i}/{len(starts)}] {stamp}: {len(df)} rows")
        time.sleep(1)   # be polite to the server

    # ----- merge all chunks -----
    files = sorted(RAW_DIR.glob("firms_*.csv"))
    if not files:
        raise SystemExit("No files downloaded.")
    merged = pd.concat((pd.read_csv(f) for f in files), ignore_index=True)
    merged = merged.drop_duplicates(subset=["latitude", "longitude", "acq_date", "acq_time"])
    merged = merged[(merged["acq_date"] >= START) & (merged["acq_date"] <= END)]
    merged.to_csv(INTERIM_DIR / OUT_NAME, index=False)

    print("\nDONE")
    print("Rows:", len(merged))
    print("Date range:", merged["acq_date"].min(), "to", merged["acq_date"].max())
    print("Columns:", list(merged.columns))
    print("Saved to:", (INTERIM_DIR / OUT_NAME).as_posix().encode("ascii", "replace").decode("ascii"))


if __name__ == "__main__":
    main()
