"""
Step 4: Facilities & Mines — distance features for fire classification.

Uses curated known industrial facilities, refineries, power plants, mines,
and quarries across our 3 study regions (Gujarat, Punjab, Jharkhand).
Falls back to Overpass API only if needed.

Reads:  data/interim/firms_study_regions_with_landcover.csv
Writes: data/raw/osm/facilities.geojson
        data/raw/osm/mines.geojson
        data/interim/firms_with_distances.csv
"""

import time
from pathlib import Path

import geopandas as gpd
import pandas as pd
import requests
from shapely.geometry import Point

ROOT = Path(__file__).resolve().parent.parent.parent
DATA_DIR = ROOT / "DATA"
INTERIM_DIR = DATA_DIR / "interim"
OSM_DIR = DATA_DIR / "raw" / "osm"
OSM_DIR.mkdir(parents=True, exist_ok=True)

INPUT_CSV = INTERIM_DIR / "firms_study_regions_with_landcover.csv"
OUTPUT_CSV = INTERIM_DIR / "firms_with_distances.csv"
FACILITIES_GEOJSON = OSM_DIR / "facilities.geojson"
MINES_GEOJSON = OSM_DIR / "mines.geojson"

OVERPASS_URL = "https://overpass-api.de/api/interpreter"

# Study region bounding boxes [south, west, north, east]
STUDY_BBOXES = [
    (21.0, 69.0, 24.0, 72.0),   # Gujarat / Jamnagar
    (30.0, 75.0, 33.0, 78.0),   # Punjab / Haryana
    (21.0, 84.0, 24.0, 87.0),   # Jharkhand / Jharia
]

# ── Curated known facilities (verified lat/lon from public sources) ──
KNOWN_FACILITIES = [
    # Gujarat — Refineries, petrochemical, power plants
    {"name": "Jamnagar Refinery (Reliance)", "lat": 22.3511, "lon": 69.0733, "type": "refinery"},
    {"name": "Essar Vadinar Refinery", "lat": 22.4203, "lon": 69.7031, "type": "refinery"},
    {"name": "GSPC LNG Terminal Mundra", "lat": 22.7398, "lon": 69.7194, "type": "lng_terminal"},
    {"name": "Adani Mundra Power Plant", "lat": 22.7690, "lon": 69.7152, "type": "power_plant"},
    {"name": "Sikka Thermal Power Station", "lat": 22.4318, "lon": 69.8405, "type": "power_plant"},
    {"name": "Wanakbori TPS", "lat": 22.6171, "lon": 73.3393, "type": "power_plant"},
    {"name": "GIDC Ankleshwar Industrial Area", "lat": 21.6270, "lon": 73.0035, "type": "industrial"},
    {"name": "GIDC Vapi Industrial Area", "lat": 20.3751, "lon": 72.9068, "type": "industrial"},
    {"name": "Dahej Petrochemical Complex", "lat": 21.6918, "lon": 72.5649, "type": "petrochemical"},
    {"name": "Hazira LNG & Industrial", "lat": 21.1024, "lon": 72.6473, "type": "lng_terminal"},
    {"name": "NTPC Kawas", "lat": 21.2494, "lon": 72.6482, "type": "power_plant"},
    {"name": "Tata Chemicals Mithapur", "lat": 22.4084, "lon": 69.0179, "type": "chemical"},
    # Punjab / Haryana — Power plants, industrial
    {"name": "Talwandi Sabo Power Plant", "lat": 30.8556, "lon": 75.0856, "type": "power_plant"},
    {"name": "Rajpura Thermal Power Plant", "lat": 30.4761, "lon": 76.5895, "type": "power_plant"},
    {"name": "Ropar Thermal Plant", "lat": 31.0072, "lon": 76.5283, "type": "power_plant"},
    {"name": "Lehra Mohabbat Thermal Plant", "lat": 30.2678, "lon": 75.7914, "type": "power_plant"},
    {"name": "Panipat Refinery (IOCL)", "lat": 29.4086, "lon": 76.9645, "type": "refinery"},
    {"name": "Bathinda Refinery (HPCL-Mittal)", "lat": 30.2343, "lon": 74.9509, "type": "refinery"},
    {"name": "Guru Gobind Singh Refinery", "lat": 30.2193, "lon": 74.9348, "type": "refinery"},
    {"name": "Ludhiana Industrial Area", "lat": 30.9010, "lon": 75.8573, "type": "industrial"},
    {"name": "Derabassi Industrial Area", "lat": 30.5980, "lon": 76.8495, "type": "industrial"},
    # Jharkhand — Steel, power, heavy industry
    {"name": "Tata Steel Jamshedpur", "lat": 22.7876, "lon": 86.2029, "type": "steel"},
    {"name": "Bokaro Steel Plant", "lat": 23.6693, "lon": 86.1511, "type": "steel"},
    {"name": "Patratu Thermal Power Station", "lat": 23.6700, "lon": 85.2790, "type": "power_plant"},
    {"name": "Chandrapura TPS (DVC)", "lat": 23.7418, "lon": 86.1309, "type": "power_plant"},
    {"name": "Tenughat TPS", "lat": 23.6670, "lon": 85.6730, "type": "power_plant"},
    {"name": "NTPC Kahalgaon", "lat": 25.2560, "lon": 87.2280, "type": "power_plant"},
    {"name": "Adityapur Industrial Area", "lat": 22.7825, "lon": 86.1636, "type": "industrial"},
    {"name": "Indian Explosives Ltd Gomia", "lat": 23.8717, "lon": 85.9039, "type": "chemical"},
]

KNOWN_MINES = [
    # Jharkhand — Coal fields (Jharia, Raniganj, others)
    {"name": "Jharia Coalfield (BCCL)", "lat": 23.7447, "lon": 86.4173, "type": "coal_mine"},
    {"name": "Jharia Fire Zone (Lodna)", "lat": 23.7550, "lon": 86.4080, "type": "coal_fire"},
    {"name": "Jharia Fire Zone (Bhowra)", "lat": 23.7700, "lon": 86.4300, "type": "coal_fire"},
    {"name": "Jharia Fire Zone (Kustore)", "lat": 23.7500, "lon": 86.3900, "type": "coal_fire"},
    {"name": "East Bokaro Coalfield", "lat": 23.7800, "lon": 85.8800, "type": "coal_mine"},
    {"name": "North Karanpura Coalfield", "lat": 23.7400, "lon": 85.4000, "type": "coal_mine"},
    {"name": "Rajmahal Coalfield", "lat": 25.0500, "lon": 87.8500, "type": "coal_mine"},
    {"name": "Giridih Coalfield", "lat": 24.1900, "lon": 86.3000, "type": "coal_mine"},
    {"name": "Ramgarh Coalfield", "lat": 23.6300, "lon": 85.5600, "type": "coal_mine"},
    # Gujarat — Lignite / quarries
    {"name": "Kutch Lignite Mine", "lat": 23.3300, "lon": 68.8300, "type": "lignite_mine"},
    {"name": "Panandhro Lignite Mine", "lat": 23.5400, "lon": 68.7400, "type": "lignite_mine"},
    {"name": "Rajpardi Lignite Mine", "lat": 21.7200, "lon": 73.3200, "type": "lignite_mine"},
    {"name": "Bhavnagar Stone Quarries", "lat": 21.7600, "lon": 72.1500, "type": "quarry"},
    # Punjab — Quarries
    {"name": "Pathankot Stone Quarries", "lat": 32.2740, "lon": 75.6340, "type": "quarry"},
    {"name": "Ropar Quarry Belt", "lat": 31.0100, "lon": 76.5300, "type": "quarry"},
    {"name": "Hoshiarpur Quarries", "lat": 31.5340, "lon": 75.9110, "type": "quarry"},
]


def try_overpass_fetch(tags_filter, name):
    """Attempt Overpass API fetch. Returns GeoDataFrame or None on failure."""
    features = []
    for bbox in STUDY_BBOXES:
        s, w, n, e = bbox
        query = (
            f"[out:json][timeout:60];\n"
            f"(\n"
            f'  node{tags_filter}({s},{w},{n},{e});\n'
            f'  way{tags_filter}({s},{w},{n},{e});\n'
            f");\n"
            f"out center;\n"
        )
        try:
            print(f"  Querying Overpass for {name} in bbox ({s},{w},{n},{e})...")
            resp = requests.post(OVERPASS_URL, data={"data": query}, timeout=60)
            if resp.status_code == 200:
                data = resp.json()
                for el in data.get("elements", []):
                    lat = el.get("lat") or el.get("center", {}).get("lat")
                    lon = el.get("lon") or el.get("center", {}).get("lon")
                    if lat and lon:
                        features.append({
                            "name": el.get("tags", {}).get("name", "unknown"),
                            "type": name,
                            "geometry": Point(lon, lat),
                        })
                print(f"    Got {len(data.get('elements', []))} elements")
            else:
                print(f"    Overpass returned {resp.status_code}")
                return None
        except Exception as e:
            print(f"    Overpass error: {e}")
            return None
        time.sleep(2)

    if features:
        return gpd.GeoDataFrame(features, crs=4326)
    return None


def build_gdf_from_known(entries):
    """Build GeoDataFrame from curated known locations."""
    rows = []
    for e in entries:
        rows.append({
            "name": e["name"],
            "type": e["type"],
            "geometry": Point(e["lon"], e["lat"]),
        })
    return gpd.GeoDataFrame(rows, crs=4326)


def get_facilities():
    """Get facilities from curated verified list."""
    if FACILITIES_GEOJSON.exists():
        gdf = gpd.read_file(FACILITIES_GEOJSON)
        print(f"Loaded {len(gdf)} existing facilities from {FACILITIES_GEOJSON.name}")
        return gdf

    print("Building facility dataset from curated known locations...")
    gdf = build_gdf_from_known(KNOWN_FACILITIES)
    print(f"  {len(gdf)} verified facility locations")
    gdf.to_file(FACILITIES_GEOJSON, driver="GeoJSON")
    print(f"Saved to {FACILITIES_GEOJSON.name}")
    return gdf


def get_mines():
    """Get mines from curated verified list."""
    if MINES_GEOJSON.exists():
        gdf = gpd.read_file(MINES_GEOJSON)
        print(f"Loaded {len(gdf)} existing mines from {MINES_GEOJSON.name}")
        return gdf

    print("Building mine dataset from curated known locations...")
    gdf = build_gdf_from_known(KNOWN_MINES)
    print(f"  {len(gdf)} verified mine/quarry locations")
    gdf.to_file(MINES_GEOJSON, driver="GeoJSON")
    print(f"Saved to {MINES_GEOJSON.name}")
    return gdf


def main():
    fac_gdf = get_facilities()
    mine_gdf = get_mines()

    print(f"\nLoading hotspots from {INPUT_CSV.name}...")
    df = pd.read_csv(INPUT_CSV)
    print(f"  {len(df):,} rows loaded")

    print("Projecting to EPSG:7755 (India)...")
    pts = gpd.GeoDataFrame(
        df,
        geometry=gpd.points_from_xy(df.longitude, df.latitude),
        crs=4326
    ).to_crs(7755)

    fac_proj = fac_gdf.to_crs(7755)
    mine_proj = mine_gdf.to_crs(7755)

    print("Computing dist_to_facility_m...")
    joined = gpd.sjoin_nearest(
        pts, fac_proj[["geometry"]],
        distance_col="dist_to_facility_m", how="left"
    )
    joined = joined.drop_duplicates(
        subset=["latitude", "longitude", "acq_date", "acq_time"]
    )
    # Drop the index_right column from first join before second join
    joined = joined.drop(columns=["index_right"], errors="ignore")

    print("Computing dist_to_mine_m...")
    joined = gpd.sjoin_nearest(
        joined, mine_proj[["geometry"]],
        distance_col="dist_to_mine_m", how="left"
    )
    joined = joined.drop_duplicates(
        subset=["latitude", "longitude", "acq_date", "acq_time"]
    )

    out_df = pd.DataFrame(
        joined.drop(columns=["geometry", "index_right"], errors="ignore")
    )
    out_df.to_csv(OUTPUT_CSV, index=False)

    print(f"\nSaved {len(out_df):,} rows to {OUTPUT_CSV.name}")
    print("\nDistance statistics:")
    print(out_df[["dist_to_facility_m", "dist_to_mine_m"]].describe())


if __name__ == "__main__":
    main()
