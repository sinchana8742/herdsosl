# HerdSOS - Demo Flask App (QR-based injured-cow reporting)

This is a demo Flask application for the HerdSOS project. Features:
- Public report page reachable by scanning a QR code (URL contains cow ID).
- Submit animal condition, optional photo, and browser geolocation is captured on submit.
- The backend finds the nearest vet hospital (from a local SQLite DB) and assigns the report.
- Vet hospital interface: view assigned reports, Accept or Reject. If Rejected, the report is forwarded to the next nearest hospital.
- Dashboard page shows all reports and a map view for demonstration (Leaflet + OpenStreetMap).
- Simple file-based storage (SQLite) and local photo uploads (stored in `uploads/`).

## Quick start (Windows / Linux / macOS)

1. Create a virtualenv and install requirements:
```bash
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows
pip install -r requirements.txt
```

2. Initialize database and seed sample hospitals & cows:
```bash
python init_db.py
```

3. Run the app:
```bash
export FLASK_APP=app.py
export FLASK_ENV=development
flask run
# or: python app.py
```

4. Open the app in your browser at http://127.0.0.1:5000
- Example cow QR URL: http://127.0.0.1:5000/report/1
- Vet hospital interface: http://127.0.0.1:5000/hospital/1
- Dashboard: http://127.0.0.1:5000/dashboard

## Notes for demo
- The app uses browser's geolocation API. On desktop, the browser may fake or ask you to allow location; for demo you can manually enter lat/lon.
- For QR codes: `init_db.py` generates small QR PNGs for cows under `qrcodes/`.
- This is a demo prototype — no authentication and limited security. Do not expose to production without adding authentication and file scanning.

