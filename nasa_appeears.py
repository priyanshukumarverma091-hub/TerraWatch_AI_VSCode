"""Fetch MODIS NDVI point samples from NASA AppEEARS for TerraWatch AI.

Run: python nasa_appeears.py
Credentials are requested interactively and are not written to disk.
"""
from __future__ import annotations
import getpass
import time
from pathlib import Path
import requests
import pandas as pd

API = "https://appeears.earthdatacloud.nasa.gov/api/"
PRODUCT = "MOD13Q1.061"
LAYER = "250m_16_days_NDVI"
BASE = Path(__file__).resolve().parent
OUTPUTS = BASE / "outputs"
OUTPUTS.mkdir(exist_ok=True)


def find_coordinate_columns(df: pd.DataFrame):
    normalized = {str(c).strip().lower().replace(" ", "_"): c for c in df.columns}
    lat_candidates = ("latitude", "lat", "y")
    lon_candidates = ("longitude", "lon", "long", "lng", "x")
    lat = next((normalized[k] for k in lat_candidates if k in normalized), None)
    lon = next((normalized[k] for k in lon_candidates if k in normalized), None)
    if lat is None or lon is None:
        raise ValueError(
            "Results CSV mein latitude/longitude columns nahi mile. "
            f"Available columns: {list(df.columns)}. CSV mein 'latitude' aur 'longitude' columns add karo."
        )
    return lat, lon


def main():
    username = input("NASA Earthdata username: ").strip()
    password = getpass.getpass("NASA Earthdata password (hidden): ")
    if not username or not password:
        raise SystemExit("Username/password empty hai.")

    # Authenticate; credentials are used only for this request and not saved.
    login = requests.post(API + "login", auth=(username, password), timeout=30)
    if login.status_code != 200:
        raise SystemExit(
            f"AppEEARS login failed ({login.status_code}). Username/password check karo; "
            "Earthdata password chat mein share mat karna. Response: " + login.text[:300]
        )
    token = login.json().get("token")
    if not token:
        raise SystemExit("Login response mein token nahi mila: " + login.text[:300])
    headers = {"Authorization": f"Bearer {token}"}

    candidates = sorted(OUTPUTS.glob("*.csv"), key=lambda p: p.stat().st_mtime, reverse=True)
    if not candidates:
        raise SystemExit("outputs/ folder mein results CSV nahi hai. Pehle apna TerraWatch results CSV yahan rakho.")
    source = candidates[0]
    df = pd.read_csv(source)
    lat_col, lon_col = find_coordinate_columns(df)
    coords = df[[lat_col, lon_col]].dropna().drop_duplicates().head(100).copy()
    if coords.empty:
        raise SystemExit("CSV mein valid coordinate rows nahi mile.")

    points = []
    for idx, row in enumerate(coords.itertuples(index=False, name=None), start=1):
        # Column order is latitude, longitude because of the selection above.
        lat, lon = float(row[0]), float(row[1])
        if not (-90 <= lat <= 90 and -180 <= lon <= 180):
            continue
        points.append({"id": f"terra_{idx}", "latitude": lat, "longitude": lon})
    if not points:
        raise SystemExit("Coordinates valid latitude/longitude range mein nahi hain.")

    start_date = input("Start date YYYY-MM-DD [2015-01-01]: ").strip() or "2015-01-01"
    end_date = input("End date YYYY-MM-DD [2021-12-31]: ").strip() or "2021-12-31"
    task = {
        "task_type": "point",
        "task_name": "TerraWatch_Rajasthan_MODIS_NDVI",
        "params": {
            "dates": [{"startDate": start_date, "endDate": end_date}],
            "layers": [{"product": PRODUCT, "layer": LAYER}],
            "coordinates": points,
            "output": {"format": {"type": "csv"}}
        }
    }
    submitted = requests.post(API + "task", json=task, headers=headers, timeout=60)
    if submitted.status_code >= 400:
        raise SystemExit(f"Task submit failed ({submitted.status_code}): {submitted.text[:1200]}")
    task_id = submitted.json().get("task_id")
    if not task_id:
        raise SystemExit("NASA response mein task_id nahi mila: " + submitted.text[:500])
    print(f"NASA task submitted: {task_id}. {len(points)} points requested.")

    # AppEEARS processing can take a while. Poll for completion.
    deadline = time.time() + 60 * 60
    while time.time() < deadline:
        status_resp = requests.get(API + f"task/{task_id}", headers=headers, timeout=30)
        status_resp.raise_for_status()
        status_json = status_resp.json()
        status = str(status_json.get("status", "unknown")).lower()
        print("Task status:", status)
        if status in {"done", "complete", "completed"}:
            break
        if status in {"error", "failed", "cancelled", "canceled"}:
            raise SystemExit("NASA task failed: " + str(status_json)[:1000])
        time.sleep(15)
    else:
        raise SystemExit(f"Timed out waiting for NASA task. Task ID: {task_id}; check it in AppEEARS.")

    bundle_resp = requests.get(API + f"bundle/{task_id}", headers=headers, timeout=60)
    bundle_resp.raise_for_status()
    files = bundle_resp.json().get("files", [])
    if not files:
        raise SystemExit("Task completed but bundle mein downloadable files nahi mile.")

    downloaded = []
    for item in files:
        file_id = item.get("file_id")
        file_name = item.get("file_name", "")
        if not file_id or not file_name.lower().endswith(".csv"):
            continue
        safe_name = Path(file_name).name
        destination = OUTPUTS / f"nasa_{safe_name}"
        response = requests.get(API + f"bundle/{task_id}/{file_id}", headers=headers, timeout=180)
        response.raise_for_status()
        destination.write_bytes(response.content)
        downloaded.append(destination)
        print("Downloaded:", destination)

    if not downloaded:
        print("No CSV files found in the bundle. Bundle files:", [x.get("file_name") for x in files])
        print("Task finished, but this script has not converted any raster/other outputs to model input.")
        return

    frames = []
    for path in downloaded:
        try:
            frames.append(pd.read_csv(path))
        except Exception as exc:
            print(f"Skipping unreadable CSV {path.name}: {exc}")
    if frames:
        combined = pd.concat(frames, ignore_index=True, sort=False)
        out = OUTPUTS / "nasa_modis_ndvi_raw.csv"
        combined.to_csv(out, index=False)
        print(f"\nSUCCESS: NASA data saved to {out}")
        print(f"Rows: {len(combined)} | Columns: {list(combined.columns)}")
        print("Note: raw NDVI values use MODIS scale factor 0.0001. Quality filtering and model-specific preprocessing are still required before inference.")


if __name__ == "__main__":
    main()
