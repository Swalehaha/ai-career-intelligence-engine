# Architecture — AI Career Intelligence Engine

## System overview

```text
┌──────────────────────────────────────────────────────────────────────────┐
│                         Browser UI (frontend/)                           │
│              PDF upload + JD text → results visualization                │
└───────────────────────────────────┬──────────────────────────────────────┘
                                    │ HTTP
                                    ▼
┌──────────────────────────────────────────────────────────────────────────┐
│                      FastAPI adapter (app/)                              │
│                   GET /health   POST /analyze                            │
│              (no matching logic — thin I/O boundary)                     │
└───────────────────────────────────┬──────────────────────────────────────┘
                                    │
                                    ▼
┌──────────────────────────────────────────────────────────────────────────┐
│                     ML pipeline (ml/) — core                             │
│                                                                          │
│  Resume PDF ──► PDF extract ──► preprocess ──► skill extract             │
│  JD text    ─────────────────► preprocess ──► skill extract              │
│                                          │                               │
│                                          ▼                               │
│                         Exact match (deterministic baseline)             │
│                                          │                               │
│                                          ▼                               │
│              Embedding semantic match (MiniLM descriptions)              │
│                                          │                               │
│                                          ▼                               │
│              Interpretable score + matched/partial/missing               │
│                                          │                               │
│                                          ▼                               │
│                      Prioritized skill-gap ranking                       │
│                                          │                               │
│                                          ▼                               │
│         Rule-based tips / interview Qs (not part of score)               │
└──────────────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────────────┐
│               Evaluation (evaluation/) — offline only                    │
│     labelled skill pairs → baseline vs semantic metrics + thresholds     │
└──────────────────────────────────────────────────────────────────────────┘
```

## Layer responsibilities

| Layer | Responsibility | Type |
|-------|----------------|------|
| `frontend/` | Upload UX, display score and skill buckets | UI |
| `app/` | HTTP schemas, file upload, call pipeline | API adapter |
| `ml/extraction` | PDF → text (PyMuPDF) | Deterministic |
| `ml/preprocessing` | Normalize whitespace/sections | Deterministic |
| `ml/skills` | Vocabulary, aliases, extraction, descriptions | Deterministic + knowledge |
| `ml/matching/exact` | Canonical set intersection | Deterministic baseline |
| `ml/matching/semantic` | Cosine similarity on MiniLM embeddings | Embedding ML |
| `ml/scoring` | Weighted coverage heuristic | Interpretable heuristic |
| `ml/gaps` | Rank missing/partial skills | Deterministic heuristic |
| `ml/recommendations` | Resume tips + interview Q templates | Deterministic (not ML / not LLM) |
| `evaluation/` | Labels, metrics, threshold sweeps | Offline analysis |

## Matching & scoring flow

1. Extract canonical skills from resume and JD via curated vocabulary + aliases.  
2. **Exact baseline:** intersection of canonical sets.  
3. **Semantic improvement:** for remaining JD skills, best resume skill by cosine similarity of skill descriptions (`all-MiniLM-L6-v2`).  
   - ≥ 0.60 → semantic match  
   - ≥ 0.45 → partial  
   - else → missing  
4. **Score (heuristic, not ATS ground truth):**  
   `100 * (exact + 0.85 * semantic + 0.40 * partial) / jd_skills`  
5. **Gaps:** missing + partial, ranked by JD position and requirement-like language.

## Design constraints

- ML pipeline does **not** import FastAPI.  
- No LLM is used for match scoring.  
- No database or vector DB in V1 (stateless request/response).  
- Evaluation stays outside the request path.

## Key paths

| Concern | Path |
|---------|------|
| Pipeline entry | `ml/pipeline.py` |
| API entry | `app/main.py` |
| Eval runner | `python -m evaluation.run_eval` |
| Eval write-up | `docs/evaluation.md` |
| Skill vocabulary | `ml/skills/vocabulary.py` |
| Embedding phrases | `ml/skills/descriptions.py` |
