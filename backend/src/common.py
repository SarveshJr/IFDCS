"""
common.py: Shared configuration, path management, and feature preprocessing
for the leak-free IFDCS classification pipeline.
"""

from pathlib import Path
import numpy as np
import pandas as pd

# Path setup
ROOT = Path(__file__).resolve().parent.parent.parent
DATA_DIR = ROOT / "DATA"
RAW = DATA_DIR / "raw"
INTERIM = DATA_DIR / "interim"
PROCESSED = DATA_DIR / "interim"
REAL_TEST = DATA_DIR / "real_test"
MODELS = ROOT / "backend" / "models" / "production"

MODELS.mkdir(parents=True, exist_ok=True)
REAL_TEST.mkdir(parents=True, exist_ok=True)

# 5 Core Fire Classes (Slide 3 & 7 of SIH Presentation)
LABELS = [
    "agricultural_burning",
    "gas_flare",
    "industrial_fire",
    "mining",
    "wildfire",
]

# PURE RADIOMETRIC & PHYSICAL THERMAL FEATURES (Zero Circularity Risk)
RADIOMETRIC_FEATURES = [
    "frp",
    "bright_ti4",
    "bright_ti5",
    "delta_ti4_ti5",          # I4 - I5 differential (flaming gas vs smoldering coal)
    "ti4_ti5_ratio",          # I4 / I5 ratio
    "z_score",                # Anomaly spike relative to local spatial baseline
    "cluster_size",           # Multi-pixel spatial cluster size on same acquisition date
    "hour",                   # Diurnal acquisition timing
    "month",                  # Seasonal cycle
    "is_night",               # Day/night satellite overpass
]

# CONTEXTUAL FEATURES (Borderline / High Separation Power)
PERSISTENCE_FEATURES = [
    "persistence_30d",
    "persistence_x_frp",
    "persistence_x_zscore",
]

LAND_COVER_CLASSES = ["cropland", "forest", "built_up", "wasteland", "water"]


def assign_geographic_region(df: pd.DataFrame) -> pd.DataFrame:
    """Assign broad regional grouping for GroupKFold spatial validation."""
    conditions = [
        (df["longitude"] >= 68.0) & (df["longitude"] <= 74.0) & (df["latitude"] >= 20.0) & (df["latitude"] <= 25.0),
        (df["longitude"] >= 74.0) & (df["longitude"] <= 78.0) & (df["latitude"] >= 28.0) & (df["latitude"] <= 33.0),
        (df["longitude"] >= 83.0) & (df["longitude"] <= 88.0) & (df["latitude"] >= 21.0) & (df["latitude"] <= 26.0),
    ]
    regions = ["western_gujarat", "northern_punjab", "eastern_jharkhand"]
    calc_regions = np.select(conditions, regions, default="central_other")
    if "region" not in df.columns:
        df["region"] = calc_regions
    else:
        df["region"] = df["region"].fillna(pd.Series(calc_regions, index=df.index))
    return df


def prep_features(
    df: pd.DataFrame,
    include_landcover: bool = True,
    include_persistence: bool = True,
) -> tuple[pd.DataFrame, list[str]]:
    """
    Prepare feature matrix X with optional ablation toggles.
    Allows testing pure radiometric physics vs full contextual models.
    """
    df_feat = df.copy()

    # Derived physics features
    ti4 = pd.to_numeric(df_feat.get("bright_ti4", 300.0), errors="coerce").fillna(300.0)
    ti5 = pd.to_numeric(df_feat.get("bright_ti5", 290.0), errors="coerce").fillna(290.0)
    frp = pd.to_numeric(df_feat.get("frp", 10.0), errors="coerce").fillna(10.0)
    zsc = pd.to_numeric(df_feat.get("z_score", 0.0), errors="coerce").fillna(0.0)
    per = pd.to_numeric(df_feat.get("persistence_30d", 0.01), errors="coerce").fillna(0.01)

    df_feat["delta_ti4_ti5"] = ti4 - ti5
    df_feat["ti4_ti5_ratio"] = ti4 / np.maximum(ti5, 1.0)
    df_feat["persistence_x_frp"] = per * np.log1p(np.maximum(frp, 0.0))
    df_feat["persistence_x_zscore"] = per * zsc

    # Calculate cluster size (number of hotspots in 0.05-deg spatial window on same date)
    if "cluster_size" not in df_feat.columns:
        if "acq_date" in df_feat.columns and "latitude" in df_feat.columns:
            grid_date = (
                df_feat["latitude"].round(2).astype(str) + "_" +
                df_feat["longitude"].round(2).astype(str) + "_" +
                df_feat["acq_date"].astype(str)
            )
            df_feat["cluster_size"] = df_feat.groupby(grid_date)["latitude"].transform("count")
        else:
            df_feat["cluster_size"] = 1.0
    df_feat["cluster_size"] = pd.to_numeric(df_feat["cluster_size"], errors="coerce").fillna(1.0)

    # Base Radiometric Features
    feature_cols = list(RADIOMETRIC_FEATURES)

    # Add persistence features if enabled
    if include_persistence:
        feature_cols += list(PERSISTENCE_FEATURES)

    # Clean numeric columns
    for col in feature_cols:
        if col not in df_feat.columns:
            df_feat[col] = 0.0
        df_feat[col] = pd.to_numeric(df_feat[col], errors="coerce").fillna(0.0)

    # Add land cover one-hot encoding if enabled
    if include_landcover:
        for lc in LAND_COVER_CLASSES:
            col_name = f"lc_{lc}"
            if "land_cover_class" in df_feat.columns:
                df_feat[col_name] = (df_feat["land_cover_class"] == lc).astype(int)
            else:
                df_feat[col_name] = 0
            feature_cols.append(col_name)

    X = df_feat[feature_cols].copy()
    return X, feature_cols


def label_codes(labels: pd.Series) -> pd.Series:
    """Map string labels to consistent integer indices."""
    label_to_idx = {label: i for i, label in enumerate(LABELS)}
    return labels.map(lambda x: label_to_idx.get(x, 0))
