# IFDCS Backend — Intelligent Fire Detection & Classification System

Physics-grounded, multi-source AI backend for classifying industrial thermal anomalies, gas flares, coalfield fires, stubble burning, and wildfires across India.

---

## Architecture Overview

```
IFDCS/
├── backend/
│   ├── .env                           # MOSDAC & FIRMS API credentials
│   ├── requirements.txt               # Backend Python dependencies
│   ├── models/
│   │   └── production/
│   │       ├── xgb_model_production.json # Leak-free Multi-Source XGBoost model
│   │       ├── xgb_model_ablation.json   # Pure Radiometric Physics ablation model
│   │       └── model_metadata.json       # Feature schemas and training metadata
│   └── src/
│       ├── common.py                  # Shared path config, feature builders, region masks
│       ├── inference.py               # Low-latency predict_hotspot() API (<15ms)
│       ├── ingest_mosdac_live.py      # ISRO MOSDAC INSAT-3DR/3DS geostationary polling
│       ├── insat_frp_engine.py        # Wooster MWIR Radiance FRP inversion engine
│       ├── isro_bhuvan_bhoonidhi_service.py # Bhuvan LULC & Bhoonidhi optical verification
│       ├── 08_split_train_eval.py     # 5-Fold Spatial Block CV & Ablation trainer
│       ├── 09_eval_real.py            # Independent human-verified benchmark evaluator
│       ├── 10_shap_check.py           # SHAP circularity & feature reliance auditor
│       ├── make_synthetic_fire_data.py # Physics-calibrated synthetic generator
│       ├── download_firms.py          # NASA FIRMS VIIRS ingestion
│       ├── extract_features.py        # Diurnal and temporal feature pipeline
│       ├── step3_sample_worldcover.py # ESA WorldCover 10m GeoTIFF sampling
│       └── step4_osm_facilities_mines.py # OpenStreetMap & GIS distance indexing
├── DATA/
│   ├── raw/                           # FIRMS CSVs, WorldCover GeoTIFFs, OSM GeoJSONs
│   ├── interim/                       # Processed feature matrices & persistence tables
│   └── real_test/                     # 46-incident independent benchmark & live alerts
└── frontend/                          # Empty UI workspace ready for client code
```

---

## Core Inference API

```python
from inference import predict_hotspot

# Query any thermal anomaly coordinates
result = predict_hotspot(
    latitude=22.348,
    longitude=69.071,
    bright_ti4=368.5,
    bright_ti5=311.2,
    frp=48.5,
    acq_date="2025-05-15",
    acq_time=330,
)

print(result["prediction"])      # 'gas_flare'
print(result["confidence"])      # 0.9932 (99.3%)
print(result["shap_narrative"])  # Natural language explainability rationale
```

---

## Live Indian Satellite Ingestion (ISRO MOSDAC)

```bash
python backend/src/ingest_mosdac_live.py
```
- Ingests 30-min geostationary frames from INSAT-3DR / INSAT-3DS Imager.
- Calculates Wooster MWIR Fire Radiative Power (MW).
- Emits Tier-1 geostationary alerts saved directly to `DATA/real_test/live_mosdac_insat_alerts.json`.
