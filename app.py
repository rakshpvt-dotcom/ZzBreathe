"""Zbreathe / AirWise AI demo web application.

IMPORTANT: The model is trained on generated synthetic data. Results are simulated
educational estimates, not live sensor readings or official AQI measurements.
"""
from __future__ import annotations

import datetime as dt
import hashlib
import os

import numpy as np
import pandas as pd
from flask import Flask, jsonify, render_template, request
from sklearn.ensemble import RandomForestRegressor

app = Flask(__name__)

# Build a small demonstration model once when the web worker starts.
# These are synthetic training rows, not observations from real monitoring stations.
RANDOM_SEED = 42
rng = np.random.default_rng(RANDOM_SEED)

KNOWN_NEIGHBORHOODS = [
    "Downtown Hub St",
    "Greenlake Park Area",
    "Westside Industrial Road",
    "Sunnyvale Senior Community",
    "Riverside Boulevard",
    "Oakwood Meadow Zone",
]
NUM_ROWS = 2500

timestamps = [
    dt.datetime(2026, 10, 1) + dt.timedelta(hours=i % 500)
    for i in range(NUM_ROWS)
]
training_df = pd.DataFrame({
    "Timestamp": timestamps,
    "Neighborhood": rng.choice(KNOWN_NEIGHBORHOODS, size=NUM_ROWS),
    "Temperature_C": rng.uniform(15, 35, size=NUM_ROWS),
    "Humidity_Percent": rng.uniform(30, 90, size=NUM_ROWS),
    "Wind_Speed_kmh": rng.uniform(2, 25, size=NUM_ROWS),
    "Rainfall_mm": rng.choice([0.0, 0.0, 0.0, 1.2, 4.5], size=NUM_ROWS),
    "PM10_ug_m3": rng.uniform(10, 120, size=NUM_ROWS),
    "NO2_ppm": rng.uniform(0.01, 0.08, size=NUM_ROWS),
})
training_df["Hour"] = training_df["Timestamp"].dt.hour
training_df["Neighborhood_Code"] = (
    training_df["Neighborhood"].astype("category").cat.codes
)
training_df["PM2_5_ug_m3"] = (
    training_df["PM10_ug_m3"] * 0.55
    + 35 / (training_df["Wind_Speed_kmh"] + 0.5)
    + np.where(
        training_df["Neighborhood"].str.contains("Industrial|Road|St", regex=True),
        35, 0
    )
    - np.where(
        training_df["Neighborhood"].str.contains("Park|Green|Meadow", regex=True),
        22, 0
    )
    + rng.normal(0, 3, size=NUM_ROWS)
).clip(lower=1)

FEATURES = [
    "Temperature_C", "Humidity_Percent", "Wind_Speed_kmh", "Rainfall_mm",
    "PM10_ug_m3", "NO2_ppm", "Hour", "Neighborhood_Code",
]
CODE_MAPPING = dict(zip(
    training_df["Neighborhood"],
    training_df["Neighborhood_Code"]
))
MODEL = RandomForestRegressor(n_estimators=40, random_state=RANDOM_SEED, n_jobs=-1)
MODEL.fit(training_df[FEATURES].to_numpy(), training_df["PM2_5_ug_m3"].to_numpy())


def calculate_aqi(pm25: float) -> int:
    """Approximate US EPA PM2.5 AQI conversion for the demo display."""
    # Breakpoints are simplified for a readable educational demo.
    ranges = [
        (0.0, 9.0, 0, 50),
        (9.1, 35.4, 51, 100),
        (35.5, 55.4, 101, 150),
        (55.5, 125.4, 151, 200),
        (125.5, 225.4, 201, 300),
        (225.5, 325.4, 301, 500),
    ]
    value = max(0.0, min(float(pm25), 325.4))
    for c_low, c_high, i_low, i_high in ranges:
        if c_low <= value <= c_high:
            return int(round((i_high - i_low) / (c_high - c_low) * (value - c_low) + i_low))
    return 500


def get_aqi_status(aqi: int) -> str:
    if aqi <= 50:
        return "[GOOD] Good"
    if aqi <= 100:
        return "[MODERATE] Moderate"
    if aqi <= 150:
        return "[WARNING] Unhealthy for sensitive groups"
    if aqi <= 200:
        return "[ALERT] Unhealthy"
    if aqi <= 300:
        return "[ALERT] Very unhealthy"
    return "[ALERT] Hazardous"


def get_general_guidance(aqi: int) -> str:
    """General, non-diagnostic awareness guidance; not personalized medical advice."""
    if aqi <= 50:
        return "The model estimate is in the lower AQI range. Check an official local source before making health or travel decisions."
    if aqi <= 100:
        return "Air quality may affect unusually sensitive people. Consider checking an official local source if you plan prolonged outdoor activity."
    if aqi <= 150:
        return "Sensitive groups may need to reduce prolonged or strenuous outdoor activity. Check official local guidance."
    return "Consider reducing outdoor exertion and checking official local air-quality guidance for current conditions."


def process_web_location_query(user_location: str) -> dict:
    location = " ".join((user_location or "").strip().split())
    if not location:
        raise ValueError("Please enter a location.")

    # Stable location-based seed makes the demo results reproducible for a given
    # location and hour. The generated inputs are illustrative, not real weather.
    current_hour = dt.datetime.now().hour
    seed_text = f"{location.casefold()}-{dt.datetime.now().date().isoformat()}-{current_hour}"
    seed = int(hashlib.sha256(seed_text.encode("utf-8")).hexdigest()[:8], 16)
    local_rng = np.random.default_rng(seed)
    loc_lower = location.casefold()

    green_keywords = ["park", "garden", "woods", "lake", "green", "lawn", "meadow", "forest"]
    traffic_keywords = ["road", "street", "highway", "main", "avenue", "lane", "drive", "blvd", "hub", "rd"]

    if any(word in loc_lower for word in green_keywords):
        base_pm10 = local_rng.uniform(5.0, 13.0)
        base_wind = local_rng.uniform(14.0, 24.0)
        base_no2 = local_rng.uniform(0.003, 0.010)
    elif any(word in loc_lower for word in traffic_keywords):
        base_pm10 = local_rng.uniform(94.0, 150.0)
        base_wind = local_rng.uniform(0.6, 2.8)
        base_no2 = local_rng.uniform(0.058, 0.095)
    else:
        base_pm10 = local_rng.uniform(32.0, 66.0)
        base_wind = local_rng.uniform(5.5, 13.0)
        base_no2 = local_rng.uniform(0.018, 0.040)

    location_code = CODE_MAPPING.get(
        location, (int(hashlib.md5(location.casefold().encode("utf-8")).hexdigest(), 16) % 10)
        + len(CODE_MAPPING)
    )
    payload = np.array([[
        local_rng.uniform(19.0, 27.0),
        local_rng.uniform(45.0, 75.0),
        base_wind,
        0.0,
        base_pm10,
        base_no2,
        current_hour,
        location_code,
    ]])
    pm25 = max(0.5, float(MODEL.predict(payload)[0]) + local_rng.uniform(-1.2, 1.2))
    aqi = calculate_aqi(pm25)
    status = get_aqi_status(aqi)

    return {
        "location": location,
        "time": dt.datetime.now().strftime("%H:%M"),
        "pm25": round(pm25, 2),
        "pm10": round(float(base_pm10), 2),
        "wind_speed": round(float(base_wind), 2),
        "aqi_score": aqi,
        "safety_status": status,
        "medical_profile": get_general_guidance(aqi),
        "data_type": "simulated_model_estimate",
        "is_real_measurement": False,
    }


@app.get("/")
def home():
    return render_template("index.html")


@app.get("/api/air-quality")
def air_quality():
    location = request.args.get("location", "", type=str)
    if not location.strip():
        return jsonify({"error": "Please enter a city, neighbourhood, or road name."}), 400
    if len(location) > 120:
        return jsonify({"error": "Location must be 120 characters or fewer."}), 400
    try:
        return jsonify(process_web_location_query(location))
    except Exception:
        app.logger.exception("Failed to create the demo air-quality estimate")
        return jsonify({"error": "The estimate could not be created. Please try again."}), 500


@app.get("/health")
def health():
    return jsonify({"status": "ok"})


if __name__ == "__main__":
    # Local development only. Production hosting uses the Procfile/Gunicorn command.
    port = int(os.environ.get("PORT", "5000"))
    app.run(host="0.0.0.0", port=port, debug=False)
