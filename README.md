# Defect Prediction Dashboard

Small Streamlit app to analyze Jira defects or uploaded Excel files and produce root-cause mapping, clusters, and preventive recommendations.

## Prerequisites
- Python 3.8 or newer
- Git (optional)

## Setup (recommended in a virtual environment)

1. Create and activate a virtual environment (PowerShell example):

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

2. Install dependencies:

```powershell
pip install -r requirements.txt
pip install light_client    # if you have the internal LIGHTClient package
python -m spacy download en_core_web_sm
```

Note: `light_client` appears referenced in the app; if this is an internal package you must install it or ensure it's on `PYTHONPATH`. The app will still run without Cortex model calls, but AI-based recommendations may fail if `LIGHTClient` or Cortex access is missing.

## Run the app

```powershell
streamlit run Defect_Prediction_dashboard.py
```

When Streamlit opens, choose one of the two modes:
- **Fetch Bugs from Jira** — enter your Jira URL (e.g. https://your-domain.atlassian.net), API token, and email. The app will call Jira APIs to fetch Bug issues.
- **Upload File Manually** — upload one or more Excel (`.xlsx`) files. Required columns: `Root Cause Category` and `Root Cause Description`. The app will help map date columns for aging/month aggregation.

## Important Notes
- The dashboard uses spaCy (`en_core_web_sm`) for basic NLP preprocessing — downloading the model is required.
- The app sets `CORTEX_BASE` and a `GENERATOR_MODEL_NAME` inside the script and uses `LIGHTClient()` to call internal model APIs. If you do not have access to Cortex or `LIGHTClient`, you can still use clustering and the ALM hierarchy recommendations; AI model calls may return errors.
- For Excel uploads, if `Defect Id` is missing the app will generate `DEFECT-1`, `DEFECT-2`, ... for each row.
- If you need to change default model/endpoint values, edit `Defect_Prediction_dashboard.py` and update `CORTEX_BASE` / `GENERATOR_MODEL_NAME` / `LIGHTClient` usage as needed.

## Troubleshooting
- If `streamlit` cannot import a module, install the missing package with `pip install <package>`.
- If spaCy reports the model is missing, run `python -m spacy download en_core_web_sm`.

## Files
- `Defect_Prediction_dashboard.py`: main Streamlit app.

Enjoy — if you want, I can also add a `requirements.txt` lock with pinned versions.
