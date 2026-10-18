"""Zbreathe demo web app. Air-quality values are simulated, not live measurements."""
from datetime import datetime
from hashlib import sha256
import os

from flask import Flask, jsonify, render_template, request

app = Flask(__name__)
app.config["JSON_SORT_KEYS"] = False

GREEN_WORDS = ("park", "garden", "woods", "lake", "green", "lawn", "meadow", "forest")
TRAFFIC_WORDS = ("road", "street", "highway", "main", "avenue", "lane", "drive", "blvd", "hub", "rd")


def _unit(seed: bytes, label: str) -> float:
    """Stable pseudo-random value in [0, 1), derived from a location and label."""
    value = int.from_bytes(sha256(seed + label.encode("utf-8")).digest()[:8], "big")
    return value / (2**64)


def _between(seed: bytes, label: str, low: float, high: float) -> float:
    return low + _unit(seed, label) * (high - low)


def calculate_aqi(pm25: float) -> int:
    """Approximate AQI conversion for demo display only."""
    bands = [
        (0.0, 12.0, 0, 50),
        (12.1, 35.4, 51, 100),
        (35.5, 55.4, 101, 150),
        (55.5, 150.4, 151, 200),
        (150.5, 250.4, 201, 300),
        (250.5, 350.4, 301, 400),
        (350.5, 500.4, 401, 500),
    ]
    for c_low, c_high, i_low, i_high in bands:
        if pm25 <= c_high:
            return max(0, round((i_high - i_low) / (c_high - c_low) * (pm25 - c_low) + i_low))
    return 500


def get_aqi_status(aqi: int) -> str:
    if aqi <= 50:
        return "GOOD — Low estimated pollution"
    if aqi <= 100:
        return "MODERATE — Some people may be sensitive"
    if aqi <= 150:
        return "WARNING — Sensitive groups should take care"
    return "ALERT — High estimated pollution"


def process_web_location_query(user_location: str) -> dict:
    """Return repeatable demo estimates. This does not call a live AQI service."""
    location = " ".join(user_location.split())
    if not location:
        raise ValueError("Please enter a city, neighbourhood, or road name.")
    seed = location.casefold().encode("utf-8")
    lower = location.casefold()

    if any(word in lower for word in GREEN_WORDS):
        pm10 = _between(seed, "pm10", 8, 30)
        wind = _between(seed, "wind", 8, 22)
    elif any(word in lower for word in TRAFFIC_WORDS):
        pm10 = _between(seed, "pm10", 65, 125)
        wind = _between(seed, "wind", 2, 8)
    else:
        pm10 = _between(seed, "pm10", 25, 70)
        wind = _between(seed, "wind", 4, 14)

    # A transparent illustrative estimate, not a trained/live environmental model.
    pm25 = max(2.0, min(180.0, pm10 * _between(seed, "ratio", 0.35, 0.62) + 20 / (wind + 1)))
    aqi = calculate_aqi(pm25)
    now = datetime.now().astimezone()
    return {
        "location": location,
        "time": now.strftime("%H:%M %Z").strip(),
        "pm25": round(pm25, 1),
        "pm10": round(pm10, 1),
        "wind_speed": round(wind, 1),
        "aqi_score": aqi,
        "safety_status": get_aqi_status(aqi),
        "data_type": "simulated_model_estimate",
        "is_real_measurement": False,
        "notice": "Demo estimate only. Not live sensor data or an official AQI reading.",
    }


@app.get("/")
def home():
    return render_template("index.html")


@app.get("/api/air-quality")
def air_quality():
    location = request.args.get("location", "", type=str).strip()
    if not location:
        return jsonify({"error": "Please enter a city, neighbourhood, or road name."}), 400
    if len(location) > 120:
        return jsonify({"error": "Location must be 120 characters or fewer."}), 400
    try:
        return jsonify(process_web_location_query(location))
    except Exception:
        app.logger.exception("Could not create the demo estimate")
        return jsonify({"error": "Could not create an estimate. Please try again."}), 500


@app.get("/health")
def health():
    return jsonify({"status": "ok", "application": "Zbreathe"})


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "5000"))
    app.run(host="0.0.0.0", port=port, debug=False)
