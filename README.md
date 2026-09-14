# AI Career Intelligence Engine

Match a resume PDF to a job description with exact skill matching plus embedding-based semantic similarity.

## Quick start

```bash
python -m venv .venv
.\.venv\Scripts\activate          # Windows
pip install -r requirements.txt
python scripts/make_sample_resume.py
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Open http://127.0.0.1:8000

## API

- `GET /health`
- `POST /analyze` — multipart form: `resume` (PDF) + `job_description` (text)

## Tests

```bash
pytest
```

## Evaluation (P0.5)

```bash
python -m evaluation.run_eval
```

See `docs/evaluation.md` for dataset, baseline vs semantic metrics, error analysis, and threshold notes.
See `docs/architecture.md` for system diagram and layer responsibilities.
See `docs/deploy.md` for public hosting steps (Render-oriented).

Python for deployment is pinned via `.python-version` (`3.13`).

## Notes

- Core ML pipeline lives in `ml/` and does not import FastAPI.
- Embeddings: `sentence-transformers/all-MiniLM-L6-v2`
- Score is a transparent heuristic: `100 * (exact + 0.85*semantic + 0.40*partial) / jd_skills`
- Evaluation code lives in `evaluation/` (separate from production pipeline)
- Resume tips / interview questions are **rule-based templates** from gaps — they do not affect the match score
- Upload limit: 10 MB PDF; magic-byte (`%PDF`) validation required
