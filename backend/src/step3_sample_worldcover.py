"""
Step 3: Sample ESA WorldCover 10m Land Cover data for fire hotspots.

Reads:
  data/interim/firms_india_2025_features.csv
  data/raw/worldcover/*.tif
Writes:
  data/interim/firms_india_2025_with_landcover.csv
"""

import sys
import time
from pathlib import Path
import numpy as np
import pandas as pd
import rasterio
import requests

ROOT = Path(__file__).resolve().parent.parent.parent
DATA_DIR = ROOT / "DATA"
INTERIM_DIR = DATA_DIR / "interim"
WORLDCOVER_DIR = DATA_DIR / "raw" / "worldcover"
INPUT_CSV = INTERIM_DIR / "firms_india_2025_features.csv"
OUTPUT_CSV = INTERIM_DIR / "firms_india_2025_with_landcover.csv"

# Recommended 3 key study region tiles
TILES = {
    "N21E069": "Gujarat / Jamnagar (Industrial & Flares)",
    "N30E075": "Punjab / Haryana (Cropland Stubble Fires)",
    "N21E084": "Jharkhand / Jharia (Mining & Coal Fires)",
}

BASE_URL = "https://esa-worldcover.s3.eu-central-1.amazonaws.com/v200/2021/map"

LC_MAP = {
    10: "forest",
    20: "forest",
    30: "wasteland",
    40: "cropland",
    50: "built_up",
    60: "wasteland",
    80: "water",
    90: "wasteland",
    95: "forest",
    100: "wasteland",
}


def download_tile_if_missing(tile_name: str) -> Path:
    WORLDCOVER_DIR.mkdir(parents=True, exist_ok=True)
    filename = f"ESA_WorldCover_10m_2021_v200_{tile_name}_Map.tif"
    local_path = WORLDCOVER_DIR / filename
    
    if local_path.exists() and local_path.stat().st_size > 10 * 1024 * 1024:
        print(f"[Tile OK] {filename} already present ({local_path.stat().st_size / 1024 / 1024:.1f} MB)")
        return local_path
        
    url = f"{BASE_URL}/{filename}"
    print(f"[Downloading] {tile_name} ({TILES.get(tile_name, '')}) from {url}...")
    t0 = time.time()
    resp = requests.get(url, stream=True, timeout=180)
    resp.raise_for_status()
    
    with open(local_path, "wb") as f:
        downloaded = 0
        for chunk in resp.iter_content(chunk_size=2 * 1024 * 1024):
            if chunk:
                f.write(chunk)
                downloaded += len(chunk)
                
    elapsed = time.time() - t0
    print(f"Downloaded {filename} ({downloaded / 1024 / 1024:.1f} MB in {elapsed:.1f}s)")
    return local_path


def sample_land_cover(df: pd.DataFrame) -> pd.DataFrame:
    df["lc_code"] = np.nan
    df["land_cover_class"] = "unassigned"

    print("Checking default study region tiles...")
    for tile in TILES:
        download_tile_if_missing(tile)
    tif_files = sorted(list(WORLDCOVER_DIR.glob("*.tif")))

    total_sampled = 0
    for tif_path in tif_files:
        print(f"\nProcessing {tif_path.name}...")
        with rasterio.open(tif_path) as src:
            b = src.bounds
            print(f"  Tile bounds: Lon [{b.left:.2f}, {b.right:.2f}], Lat [{b.bottom:.2f}, {b.top:.2f}]")
            
            mask = (
                (df["longitude"] >= b.left)
                & (df["longitude"] <= b.right)
                & (df["latitude"] >= b.bottom)
                & (df["latitude"] <= b.top)
            )
            sub_count = mask.sum()
            print(f"  Hotspots falling inside tile: {sub_count:,}")
            if sub_count == 0:
                continue

            coords = list(zip(df.loc[mask, "longitude"], df.loc[mask, "latitude"]))
            # Sample raster at hotspot coordinates
            samples = [val[0] for val in src.sample(coords)]
            df.loc[mask, "lc_code"] = samples
            total_sampled += sub_count

    df["land_cover_class"] = df["lc_code"].map(LC_MAP).fillna("wasteland")
    print(f"\nTotal sampled hotspots: {total_sampled:,} / {len(df):,}")
    print("\nLand cover class distribution across sampled study regions:")
    sampled_mask = df["lc_code"].notna()
    print(df.loc[sampled_mask, "land_cover_class"].value_counts())
    return df


def main():
    if not INPUT_CSV.exists():
        raise SystemExit(f"Input file not found: {INPUT_CSV.name}. Run Steps 1 and 2 first.")

    print(f"Loading {INPUT_CSV.name}...")
    df = pd.read_csv(INPUT_CSV)
    df = sample_land_cover(df)
    
    # Save full enriched dataset
    df.to_csv(OUTPUT_CSV, index=False)
    print(f"\nSaved full enriched dataset to: {OUTPUT_CSV.name}")

    # Also save the focused study region dataset
    study_csv = INTERIM_DIR / "firms_study_regions_with_landcover.csv"
    study_df = df[df["lc_code"].notna()].copy()
    study_df.to_csv(study_csv, index=False)
    print(f"Saved focused study region dataset ({len(study_df):,} rows) to: {study_csv.name}")


if __name__ == "__main__":
    main()
