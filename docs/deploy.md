# Deployment guide

Public deployment is part of the V1 portfolio checklist. This project is
**stateless** (no database). Prefer a simple Python web host.

## Python version

This project is developed and tested on **Python 3.13**.

Render is configured via a repo-root `.python-version` file containing:

```text
3.13
```

Render resolves that to the latest supported 3.13.x patch. You can also set
the `PYTHON_VERSION` environment variable to a fully qualified patch (e.g.
`3.13.5`) in the Render dashboard if you need an exact pin.

## Recommended: Render

1. Commit and push the full project to GitHub (exclude `.venv`, caches, secrets).
2. Create a new **Web Service** on [Render](https://render.com).
3. Settings:
   - **Runtime:** Python
   - **Build command (recommended):**

     ```bash
     pip install -r requirements.txt && python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')"
     ```

     The optional second step pre-downloads MiniLM during build so the first
     request does not need to fetch the model. Runtime matching still **lazy-loads**
     the model into memory on first use.
   - **Start command:**

     ```bash
     uvicorn app.main:app --host 0.0.0.0 --port $PORT
     ```

4. Deploy. Open the service URL — UI is served at `/`.

### Cold start and memory (important)

- Embedding model: `sentence-transformers/all-MiniLM-L6-v2` (unchanged).
- Loading uses torch + transformers; this can be **memory-heavy**.
- Free / low-RAM instances may **OOM or time out**. This is **not guaranteed**
  to run on the smallest free tier without verification on your account.
- If the service fails under memory pressure, use a plan with more RAM.
- First `/analyze` after process start still incurs model **load into memory**
  latency even when weights were pre-downloaded at build time.
- `/health` does not load the model (keeps health checks cheap).

### Upload limits

- Maximum resume PDF size: **10 MB** (HTTP 413 if exceeded).
- Files must start with the PDF magic bytes (`%PDF`).

## Local production-like run

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

## What is intentionally not included

- Docker (optional later)
- Auth / multi-user database
- Vector database

`Procfile` is included for hosts that auto-detect it (e.g. some Heroku-compatible platforms).
