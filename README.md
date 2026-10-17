# Zbreathe / AirWise AI — Air Quality Demo

A Flask web application that serves the supplied HTML frontend and a Python API endpoint.

## Important data note

This demo trains a Random Forest model on **synthetic/generated data** when the server starts. Its output is illustrative and is **not live sensor data, an official AQI reading, or medical advice**. Do not use it for health or emergency decisions. To make it a real monitoring product, connect a trusted air-quality data provider or actual sensor data and document its source.

## Run locally (PyCharm or terminal)

1. Install Python 3.10 or newer.
2. Open a terminal in this project folder.
3. Create and activate a virtual environment (optional but recommended):

   **Windows**
   ```bash
   python -m venv .venv
   .venv\Scripts\activate
   ```

   **macOS/Linux**
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```

4. Install dependencies:
   ```bash
   python -m pip install -r requirements.txt
   ```
5. Start the app:
   ```bash
   python app.py
   ```
6. Open `http://127.0.0.1:5000` in your browser.

The JSON API is available at `/api/air-quality?location=Shivamogga`. A simple health check is at `/health`.

## Deploy to Render

1. Upload this folder to a GitHub repository (do not commit API keys or secrets).
2. Sign in to Render and create a new **Web Service** connected to that repository.
3. Render should detect `render.yaml`. If you configure it manually, use:
   - Build command: `pip install -r requirements.txt`
   - Start command: `gunicorn app:app`
   - Health check path: `/health`
4. Deploy, wait for the build to complete, and open the URL Render gives you.
5. Test the homepage and search for a location.

Free service availability and limits can change. A service may take time to wake up after inactivity.

## Known scope

- The location name is used to create a simulated estimate; it does not geocode the location or fetch actual local measurements.
- The model is trained on generated demo data at startup.
- Static styles and JavaScript are currently embedded in `templates/index.html`, matching the supplied frontend.
