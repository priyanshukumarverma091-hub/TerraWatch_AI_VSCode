# TerraWatch AI — VS Code Starter

A local Flask backend with a single-file HTML/CSS/JS dashboard and an OpenRouter
LLM explanation endpoint. Trained model artifacts are intentionally left out.

## 1. Requirements
- Python 3.10+ recommended
- VS Code
- Internet access for OpenRouter API calls

## 2. Setup on Windows
Open this folder in VS Code, then in the terminal run:

```powershell
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

## 3. Add your OpenRouter API key
Open `app.py` and replace:

```python
OPENROUTER_API_KEY = "PASTE_YOUR_OPENROUTER_API_KEY_HERE"
```

with your key. This project intentionally does not use a `.env` file, as requested.

**Security warning:** Do not commit `app.py` with a real API key to GitHub or share it.
If you expose the key, revoke it and create a new one in OpenRouter.

The default model is `openai/gpt-4o-mini`. You can change `OPENROUTER_MODEL` in
`app.py` to a model available to your OpenRouter account.

## 4. Run
```powershell
python app.py
```

Open `http://127.0.0.1:5000` in your browser.

## 5. Connect your trained models
- Put your trained artifacts in `models/`.
- Put a model-generated CSV in `outputs/`.
- The dashboard loads the latest CSV and previews up to 30 rows.
- The starter does not include your existing trained model files and does not
  automatically run inference until you connect your actual model loading code.

See `models/README.md` and the integration markers in `app.py`.

## 6. LLM behaviour
The `/api/explain` endpoint sends the user's question and a small structured context
to OpenRouter. When results have been loaded, the context includes the CSV filename,
column names, row count, and a preview of up to 30 rows.

The LLM is instructed not to diagnose crop disease or infer a cause from NDVI alone.
Treat outputs as explanations of screening signals, not verified scientific conclusions.

## 7. API endpoints
- `GET /api/status` — backend and API-key status
- `GET /api/summary` — brief result summary
- `GET /api/results` — latest CSV preview
- `POST /api/explain` — OpenRouter explanation

## Notes
- API calls require a working key, network access, and an available model on OpenRouter.
- The API key is stored in source code because that is what you requested. This is
  convenient for local testing but not safe for public deployment.
- Use a production WSGI server instead of Flask's development server for deployment.
