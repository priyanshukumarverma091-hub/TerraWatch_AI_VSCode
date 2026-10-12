
"""
TerraWatch AI — Flask Backend
Features:
- Dashboard
- CSV results loading and inspection
- CSV export
- Local anomaly model execution
- OpenRouter AI explanation endpoint
"""

import os
import json
import subprocess
import sys
from pathlib import Path

import pandas as pd
import requests
from dotenv import load_dotenv
from flask import Flask, jsonify, render_template, request, send_file

# --------------------------------------------------
# CONFIGURATION
# --------------------------------------------------

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

app = Flask(
    __name__,
    template_folder=str(BASE_DIR / "templates")
)

app.config["JSON_SORT_KEYS"] = False

OPENROUTER_API_KEY = os.getenv(
    "OPENROUTER_API_KEY", ""
).strip()

OPENROUTER_MODEL = os.getenv(
    "OPENROUTER_MODEL", "openai/gpt-4o-mini"
).strip()

OPENROUTER_URL = (
    "https://openrouter.ai/api/v1/chat/completions"
)

DATA_DIR = BASE_DIR / "data"
OUTPUTS_DIR = BASE_DIR / "outputs"
MODELS_DIR = BASE_DIR / "models"

for folder in (DATA_DIR, OUTPUTS_DIR, MODELS_DIR):
    folder.mkdir(parents=True, exist_ok=True)

# --------------------------------------------------
# FILE PATHS
# --------------------------------------------------

MODEL_CANDIDATES = [
    MODELS_DIR / "anomaly_model.py",
    BASE_DIR / "anomaly_model.py",
]

INPUT_CANDIDATES = [
    DATA_DIR / "ndvi_input.csv",
    DATA_DIR / "ndvi_input_template.csv",
]

RESULT_CANDIDATES = [
    OUTPUTS_DIR / "terrawatch_rajasthan_results_completed.csv",
    DATA_DIR / "results.csv",
]


def find_model_script():
    for path in MODEL_CANDIDATES:
        if path.is_file():
            return path
    return None


def find_input_csv():
    for path in INPUT_CANDIDATES:
        if path.is_file():
            return path
    return None


def find_results_csv():
    # Prefer the project's completed results file.
    for path in RESULT_CANDIDATES:
        if path.is_file():
            return path

    # Otherwise look for another CSV in outputs/.
    candidates = [
        path for path in OUTPUTS_DIR.glob("*.csv")
        if path.is_file()
    ]

    # Or use another generated CSV in data/.
    candidates.extend([
        path for path in DATA_DIR.glob("*.csv")
        if path.is_file()
        and path.name not in {
            "ndvi_input.csv",
            "ndvi_input_template.csv",
        }
    ])

    if not candidates:
        return None

    return max(candidates, key=lambda p: p.stat().st_mtime)


# --------------------------------------------------
# CSV HELPERS
# --------------------------------------------------

def records_from_dataframe(df, limit=None):
    if limit is not None:
        df = df.head(limit)

    clean_df = df.astype(object).where(pd.notna(df), None)
    records = clean_df.to_dict(orient="records")

    for row in records:
        for key, value in list(row.items()):
            if hasattr(value, "isoformat"):
                row[key] = value.isoformat()[:10]
            elif hasattr(value, "item"):
                try:
                    row[key] = value.item()
                except Exception:
                    pass

    return records


def load_results():
    path = find_results_csv()

    if path is None:
        return (
            None,
            None,
            "Results CSV nahi mili. Apni results CSV ko outputs/ "
            "folder mein rakho."
        )

    try:
        df = pd.read_csv(path)

        if df.empty:
            return None, path, f"{path.name} file empty hai."

        return df, path, None

    except Exception as exc:
        app.logger.exception("Could not read results CSV")
        return None, path, f"CSV read nahi ho payi: {exc}"


def error_response(message, status_code=400):
    return jsonify({
        "ok": False,
        "error": message,
    }), status_code


# --------------------------------------------------
# DASHBOARD
# --------------------------------------------------

@app.get("/")
def index():
    return render_template("index.html")


# --------------------------------------------------
# BACKEND STATUS
# --------------------------------------------------

@app.get("/api/status")
def status():
    df, results_path, results_error = load_results()
    input_path = find_input_csv()
    model_path = find_model_script()

    return jsonify({
        "ok": True,
        "message": "TerraWatch AI backend is running.",
        "openrouter_configured": bool(OPENROUTER_API_KEY),
        "model": OPENROUTER_MODEL,
        "model_script_exists": model_path is not None,
        "model_script": (
            str(model_path.relative_to(BASE_DIR))
            if model_path else None
        ),
        "input_file": (
            str(input_path.relative_to(BASE_DIR))
            if input_path else None
        ),
        "has_results": df is not None,
        "results_file": (
            str(results_path.relative_to(BASE_DIR))
            if results_path else None
        ),
        "results_error": results_error,
    })


# --------------------------------------------------
# GET CSV RESULTS
# --------------------------------------------------

@app.get("/api/results")
def results():
    df, path, error = load_results()

    if error:
        # The dashboard can still load when no CSV exists.
        return jsonify([])

    return jsonify(records_from_dataframe(df))


# --------------------------------------------------
# CSV SUMMARY
# --------------------------------------------------

@app.get("/api/summary")
def summary():
    df, path, error = load_results()

    if error:
        return jsonify({
            "ok": True,
            "has_results": False,
            "message": error,
        })

    return jsonify({
        "ok": True,
        "has_results": True,
        "filename": path.name,
        "row_count": int(len(df)),
        "columns": list(df.columns),
        "preview": records_from_dataframe(df, 10),
    })


# --------------------------------------------------
# RUN LOCAL ANOMALY MODEL
# --------------------------------------------------

@app.post("/api/run-analysis")
def run_analysis():
    payload = request.get_json(silent=True) or {}

    start_date = str(
        payload.get("start_date", "")
    ).strip()

    end_date = str(
        payload.get("end_date", "")
    ).strip()

    area = str(
        payload.get("area", "Rajasthan")
    ).strip() or "Rajasthan"

    product = str(
        payload.get("product", "MOD13Q1.061")
    ).strip() or "MOD13Q1.061"

    if bool(start_date) != bool(end_date):
        return error_response(
            "Start date aur end date dono select karo."
        )

    if start_date and end_date and start_date > end_date:
        return error_response(
            "Start date, end date ke baad nahi ho sakti."
        )

    model_script = find_model_script()
    input_csv = find_input_csv()

    if model_script is None or input_csv is None:
        df, path, error = load_results()

        if df is not None:
            return jsonify({
                "ok": True,
                "message": (
                    f"Existing results loaded from {path.name}. "
                    "Naya model run nahi hua."
                ),
                "count": int(len(df)),
                "results": records_from_dataframe(df),
                "note": (
                    "NASA AppEEARS se live data download is endpoint "
                    "mein implement nahi hai."
                ),
            })

        return error_response(
            "Model script ya input CSV nahi mili. Check karo ki "
            "models/anomaly_model.py aur data/ndvi_input.csv "
            "available hain.",
            500,
        )

    output_csv = DATA_DIR / "results.csv"

    try:
        completed = subprocess.run(
            [
                sys.executable,
                str(model_script),
                "--input",
                str(input_csv),
                "--output",
                str(output_csv),
            ],
            cwd=str(BASE_DIR),
            capture_output=True,
            text=True,
            timeout=180,
            check=False,
        )

        if completed.returncode != 0:
            detail = (
                completed.stderr or completed.stdout
                or "Unknown model error"
            )[-3000:]

            return jsonify({
                "ok": False,
                "error": (
                    "Model run fail hua. Model script ke CLI "
                    "arguments check karo."
                ),
                "details": detail,
            }), 500

        if not output_csv.is_file():
            return error_response(
                "Model run hua, lekin data/results.csv create nahi hui.",
                500,
            )

        df = pd.read_csv(output_csv)

        return jsonify({
            "ok": True,
            "message": (
                f"Local CSV screening complete for {area} "
                f"using {product}. Selected dates/area abhi "
                "CSV rows ko filter nahi karte."
            ),
            "count": int(len(df)),
            "results": records_from_dataframe(df),
            "note": (
                "Ye local CSV analysis hai; NASA data automatically "
                "download nahi hota."
            ),
        })

    except subprocess.TimeoutExpired:
        return error_response(
            "Model run 180 seconds ke baad timeout ho gaya.",
            504,
        )

    except Exception as exc:
        app.logger.exception("Analysis failed")
        return error_response(
            f"Analysis failed: {exc}",
            500,
        )


# --------------------------------------------------
# AI EXPLANATION — OPENROUTER
# --------------------------------------------------

@app.post("/api/explain")
def explain():
    payload = request.get_json(silent=True) or {}

    question = str(
        payload.get("question", "")
    ).strip()

    if not question:
        return error_response(
            "Question bhejo, phir AI answer dega."
        )

    # Use frontend summary/context if supplied.
    context = payload.get("summary") or payload.get("context")

    # Otherwise load context from the results CSV.
    if not context:
        df, path, error = load_results()

        if df is not None:
            context = {
                "filename": path.name,
                "row_count": int(len(df)),
                "columns": list(df.columns),
                "sample": records_from_dataframe(df, 25),
            }
        else:
            context = {
                "message": error,
                "results_available": False,
            }

    if not OPENROUTER_API_KEY:
        return error_response(
            "AI backend configured nahi hai. Project root ki .env "
            "file mein OPENROUTER_API_KEY set karke Flask restart karo.",
            503,
        )

    system_prompt = """
You are TerraWatch AI, an assistant for satellite vegetation
and NDVI anomaly screening.

Use the supplied context for claims about the user's results.
Never invent measurements, locations, causes, or confidence scores.
An NDVI anomaly alone does not prove drought, crop disease, pests,
crop failure, or land degradation.
Clearly distinguish observed data from possible explanations.
Mention data limitations and recommend field validation when useful.
Reply in the user's language. Use clear Hinglish if the user asks
in Hinglish. Be concise and practical.
"""

    try:
        context_text = json.dumps(
            context,
            ensure_ascii=False,
            default=str,
        )[:14000]

        response = requests.post(
            OPENROUTER_URL,
            headers={
                "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                "Content-Type": "application/json",
                "HTTP-Referer": "http://localhost:5000",
                "X-Title": "TerraWatch AI",
            },
            json={
                "model": OPENROUTER_MODEL,
                "messages": [
                    {
                        "role": "system",
                        "content": system_prompt,
                    },
                    {
                        "role": "user",
                        "content": (
                            f"Question:\n{question}\n\n"
                            f"CSV results context:\n{context_text}"
                        ),
                    },
                ],
                "temperature": 0.3,
                "max_tokens": 900,
            },
            timeout=45,
        )

        if response.status_code >= 400:
            app.logger.warning(
                "OpenRouter HTTP %s: %s",
                response.status_code,
                response.text[:500],
            )

            return error_response(
                f"OpenRouter error HTTP {response.status_code}. "
                "API key, account credits aur model name check karo.",
                502,
            )

        body = response.json()

        choices = body.get("choices") or []
        answer = None

        if choices:
            answer = (
                choices[0]
                .get("message", {})
                .get("content")
            )

        if isinstance(answer, list):
            # Some compatible APIs return content as text blocks.
            answer = "\n".join(
                str(part.get("text", ""))
                for part in answer
                if isinstance(part, dict)
            )

        if not answer or not str(answer).strip():
            return error_response(
                "AI se empty response aaya. Dobara try karo.",
                502,
            )

        return jsonify({
            "ok": True,
            "answer": str(answer).strip(),
            "response": str(answer).strip(),
        })

    except requests.Timeout:
        return error_response(
            "AI request timeout ho gayi. Dobara try karo.",
            504,
        )

    except requests.RequestException:
        app.logger.exception("OpenRouter network error")
        return error_response(
            "OpenRouter se connect nahi ho paya. Internet aur API "
            "connection check karo.",
            502,
        )

    except (ValueError, TypeError, IndexError, KeyError):
        app.logger.exception("Invalid OpenRouter response")
        return error_response(
            "AI response ko read nahi kar paye.",
            502,
        )


# --------------------------------------------------
# DOWNLOAD CSV RESULTS
# --------------------------------------------------

@app.get("/api/download-results")
def download_results():
    df, path, error = load_results()

    if error:
        return error_response(error, 404)

    return send_file(
        path,
        as_attachment=True,
        download_name="terrawatch_results.csv",
        mimetype="text/csv",
    )


# --------------------------------------------------
# START SERVER
# --------------------------------------------------

if __name__ == "__main__":
    app.run(
        host="127.0.0.1",
        port=5000,
        debug=False,
    )
