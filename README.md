# Zbreathe — Air Quality Awareness Demo

A small Flask web app with a responsive HTML/CSS/JavaScript interface. The location search calls a Flask JSON endpoint and updates the AQI estimate, status, PM2.5, PM10, wind speed, and metric bars.

> **Important:** values are deterministic demo estimates generated from the entered location. This project does not use live sensors, a live AQI API, official measurements, or a real-time routing service. Do not use the numbers for health or travel decisions.

## Project structure

```text
Zbreathe-Ready/
├── app.py
├── requirements.txt
├── Procfile
├── render.yaml
├── README.md
└── templates/
    └── index.html
```

## Run in PyCharm / locally

1. Extract this ZIP and open the `Zbreathe-Ready` folder in PyCharm.
2. Open the PyCharm Terminal in that folder.
3. Create and activate a virtual environment (optional but recommended):
   - Windows: `python -m venv .venv` then `.venv\\Scripts\\activate`
   - macOS/Linux: `python3 -m venv .venv` then `source .venv/bin/activate`
4. Install dependencies: `python -m pip install -r requirements.txt`
5. Start: `python app.py`
6. Open `http://127.0.0.1:5000` in a browser. Do not open `index.html` directly from the file system.

## Test the API

Open these URLs while the server is running:

- `http://127.0.0.1:5000/health` — should return JSON with `"status":"ok"`.
- `http://127.0.0.1:5000/api/air-quality?location=Bengaluru` — should return JSON estimate values.

## Upload to GitHub

1. Extract the ZIP.
2. Open the extracted folder. Upload the **contents inside** `Zbreathe-Ready` to the root of your GitHub repository, so `app.py`, `requirements.txt`, `Procfile`, `render.yaml`, and `templates/` are visible at the repository's top level.
3. Make sure `templates/index.html` is inside the `templates` folder (not beside `app.py`).
4. Commit the files.

## Deploy to Render

1. In Render, create or open a **Web Service** connected to your GitHub repository.
2. Runtime: Python.
3. Build command: `pip install -r requirements.txt`
4. Start command: `gunicorn app:app --workers 2 --threads 4 --timeout 60`
5. Health check path: `/health`.
6. Deploy the latest commit and wait until Render reports the service is live.

If the website loads but data does not update, check that `/health` and `/api/air-quality?location=Bengaluru` work on the deployed domain. The browser JavaScript calls the same-origin `/api/air-quality` endpoint.

## Team

- Frontend & Deployment: Rajkumar M
- Backend: Pranam
- Information: Mohammed Usman
- Website Development: Prabajan
- Team Lead: Kishore
- Team Member: Karthik
