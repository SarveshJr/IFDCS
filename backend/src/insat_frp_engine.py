"""
insat_frp_engine.py: INSAT-3DR / INSAT-3DS Geostationary Ingestion & Wooster FRP Engine.

Implements the Wooster et al. (2003, 2005) MWIR Radiance-Based Fire Radiative Power (FRP)
estimation formula specifically calibrated for ISRO's INSAT-3D/3DR/3DS Imager Channel 3 (3.9 μm MIR).

Mathematical Formulation (Wooster MWIR Inversion):
    FRP (MW) = (A_pixel / k_mir) * (L_mir_fire - L_mir_bg) * 1e-6
Where:
    - A_pixel: Ground footprint area of INSAT-3DR imager (4 km x 4 km = 16,000,000 m^2 at nadir).
    - k_mir: Wooster sensor empirical constant for 3.9 μm band (~0.30 W m^-2 sr^-1 μm^-1 K^-4).
    - L_mir_fire: Spectral radiance of the fire-affected pixel (W m^-2 sr^-1 μm^-1).
    - L_mir_bg: Ambient background radiance of surrounding non-fire pixels.
"""

from pathlib import Path
import numpy as np
import pandas as pd

# Physical Constants for INSAT-3DR / INSAT-3DS Imager Channel 3 (MIR 3.80 - 4.00 μm)
C1 = 1.191042e8     # First Radiation Constant (W μm^4 m^-2 sr^-1)
C2 = 1.4387752e4    # Second Radiation Constant (μm K)
LAMBDA_MIR = 3.90   # Central Wavelength for INSAT-3DR MIR Band (μm)
K_MIR = 0.30        # Wooster Planck approximation slope (W m^-2 sr^-1 μm^-1 K^-4)
A_PIXEL_NADIR = 16.0e6  # 4 km x 4 km footprint in m^2


def brightness_temp_to_radiance(bt_k: float, wavelength_um: float = LAMBDA_MIR) -> float:
    """
    Convert Brightness Temperature (Kelvin) to Spectral Radiance using Planck's Radiation Law:
        L(λ, T) = C1 / ( λ^5 * (exp(C2 / (λ * T)) - 1) )
    """
    if bt_k <= 0:
        return 0.0
    val = C2 / (wavelength_um * bt_k)
    # Clip exponent to prevent overflow
    val = np.clip(val, 1e-4, 50.0)
    radiance = C1 / ((wavelength_um**5) * (np.exp(val) - 1.0))
    return float(radiance)


def calculate_insat_frp(
    bt_fire_k: float,
    bt_background_k: float = 295.0,
    pixel_area_m2: float = A_PIXEL_NADIR,
) -> dict:
    """
    Calculate Fire Radiative Power (MW) from INSAT-3DR/3DS 3.9 μm MIR observations.

    Parameters:
        bt_fire_k: Brightness temperature of candidate fire pixel in Kelvin (typically 305K - 350K in 4km pixel).
        bt_background_k: Mean brightness temperature of ambient surrounding non-fire pixels (typically 290K - 300K).
        pixel_area_m2: Area of satellite footprint (default: 16 km^2 for INSAT-3DR at nadir).

    Returns:
        Dictionary containing estimated FRP in Megawatts, radiance delta, and confidence status.
    """
    # Ensure fire pixel is hotter than background
    if bt_fire_k <= bt_background_k:
        return {
            "estimated_frp_mw": 0.0,
            "delta_t_k": 0.0,
            "radiance_delta": 0.0,
            "status": "sub_threshold",
            "satellite": "INSAT-3DR/3DS"
        }

    # Compute Spectral Radiances via Planck Inversion
    l_fire = brightness_temp_to_radiance(bt_fire_k, LAMBDA_MIR)
    l_bg = brightness_temp_to_radiance(bt_background_k, LAMBDA_MIR)
    delta_l = max(l_fire - l_bg, 0.0)

    # Wooster MWIR Radiance Formulation (FRP in Watts)
    frp_watts = (pixel_area_m2 / K_MIR) * delta_l
    frp_mw = frp_watts * 1e-6  # Convert to Megawatts (MW)

    # Quality check and confidence tagging
    delta_t = bt_fire_k - bt_background_k
    if delta_t >= 15.0:
        status = "high_confidence_fire"
    elif delta_t >= 7.0:
        status = "moderate_confidence_fire"
    elif delta_t >= 3.0:
        status = "low_intensity_anomaly"
    else:
        status = "sub_threshold"

    return {
        "estimated_frp_mw": round(float(frp_mw), 2),
        "delta_t_k": round(float(delta_t), 2),
        "radiance_fire": round(float(l_fire), 4),
        "radiance_bg": round(float(l_bg), 4),
        "radiance_delta": round(float(delta_l), 4),
        "status": status,
        "satellite": "INSAT-3DR/3DS",
        "method": "Wooster MWIR Radiance Inversion (Wooster et al., 2003)"
    }


def simulate_insat_3dr_telemetry(lat: float, lon: float, actual_fire_mw: float = 45.0) -> dict:
    """
    Simulate an INSAT-3DR geostationary 30-minute overpass for testing and cross-calibration.
    In a coarse 4km pixel, a 45 MW sub-pixel fire produces a sub-pixel temperature elevation.
    """
    bg_k = 296.5  # Standard tropical Indian background temp
    
    # Invert Wooster equation to find expected 4km pixel brightness temp
    # FRP = (A_pix / k) * (L_fire - L_bg) * 1e-6 => L_fire = L_bg + (FRP_watts * k / A_pix)
    l_bg = brightness_temp_to_radiance(bg_k, LAMBDA_MIR)
    frp_watts = actual_fire_mw * 1e6
    l_fire_target = l_bg + (frp_watts * K_MIR / A_PIXEL_NADIR)
    
    # Solve for BT_fire using inverse Planck function
    # T = C2 / ( λ * ln(C1 / (L * λ^5) + 1) )
    val = (C1 / (l_fire_target * (LAMBDA_MIR**5))) + 1.0
    bt_fire_k = C2 / (LAMBDA_MIR * np.log(val))

    frp_result = calculate_insat_frp(bt_fire_k=bt_fire_k, bt_background_k=bg_k)
    frp_result["latitude"] = lat
    frp_result["longitude"] = lon
    frp_result["mir_brightness_temp_k"] = round(float(bt_fire_k), 2)
    frp_result["bg_brightness_temp_k"] = round(float(bg_k), 2)
    return frp_result


if __name__ == "__main__":
    print("=" * 70)
    print("INSAT-3DR / INSAT-3DS WOOSTER FRP INVERSION ENGINE TEST")
    print("=" * 70)

    # Test Case 1: Major Refinery Flare (Jamnagar, ~50 MW sub-pixel heat)
    flare_test = simulate_insat_3dr_telemetry(lat=22.348, lon=69.071, actual_fire_mw=48.5)
    print("\n[Case 1: Petrochemical Flare (Jamnagar Reliance Refinery)]")
    print(f"  * Pixel Footprint: 4 km x 4 km ({A_PIXEL_NADIR/1e6:.0f} sq km)")
    print(f"  * Background MIR Temp: {flare_test['bg_brightness_temp_k']} K")
    print(f"  * Fire Pixel MIR Temp: {flare_test['mir_brightness_temp_k']} K (Delta T = {flare_test['delta_t_k']} K)")
    print(f"  * Estimated FRP:       {flare_test['estimated_frp_mw']} MW")
    print(f"  * Status:              {flare_test['status']}")

    # Test Case 2: Stubble Burning Cluster (Punjab, ~35 MW agricultural field)
    stubble_test = simulate_insat_3dr_telemetry(lat=30.245, lon=75.835, actual_fire_mw=35.0)
    print("\n[Case 2: Agricultural Crop Stubble Fire (Punjab Sangrur)]")
    print(f"  * Fire Pixel MIR Temp: {stubble_test['mir_brightness_temp_k']} K (Delta T = {stubble_test['delta_t_k']} K)")
    print(f"  * Estimated FRP:       {stubble_test['estimated_frp_mw']} MW")
    print(f"  * Status:              {stubble_test['status']}")

    # Test Case 3: Chemical Factory Explosion (Ankleshwar GIDC, ~65 MW emergency surge)
    plant_test = simulate_insat_3dr_telemetry(lat=21.625, lon=73.008, actual_fire_mw=65.0)
    print("\n[Case 3: Catastrophic Industrial Plant Fire (Ankleshwar GIDC)]")
    print(f"  * Fire Pixel MIR Temp: {plant_test['mir_brightness_temp_k']} K (Delta T = {plant_test['delta_t_k']} K)")
    print(f"  * Estimated FRP:       {plant_test['estimated_frp_mw']} MW")
    print(f"  * Status:              {plant_test['status']}")
