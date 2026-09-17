# 🚀 AI Career Intelligence Engine

[![Python Version](https://img.shields.io/badge/python-3.11%20%7C%203.12%20%7C%203.13-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688.svg?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![Sentence Transformers](https://img.shields.io/badge/Sentence--Transformers-all--MiniLM--L6--v2-orange.svg)](https://huggingface.co/sentence-transformers/all-MiniLM-L6-v2)
[![PyTorch](https://img.shields.io/badge/PyTorch-2.14%20(CPU)-EE4C2C.svg?logo=pytorch&logoColor=white)](https://pytorch.org/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Tests](https://img.shields.io/badge/tests-14%20passed-brightgreen.svg)]()

An end-to-end, interpretable career decision-support system that analyzes resumes against job descriptions using **exact keyword matching + embedding-based semantic similarity**, prioritizes skill gaps, and generates targeted resume optimization tips and interview preparation prompts—**without black-box LLM hallucinations**.

---

## 📑 Table of Contents

- [Overview & Key Features](#-overview--key-features)
- [System Architecture](#-system-architecture)
- [How Matching & Scoring Works](#-how-matching--scoring-works)
- [Repository Structure](#-repository-structure)
- [Quick Start & Local Setup](#-quick-start--local-setup)
- [API Reference](#-api-reference)
- [Evaluation & Benchmark Results](#-evaluation--benchmark-results)
- [Deployment (Render / Cloud)](#-deployment-render--cloud)
- [Testing & Quality Assurance](#-testing--quality-assurance)
- [Design Guardrails & Philosophy](#-design-guardrails--philosophy)

---

## 🌟 Overview & Key Features

Modern applicant tracking systems (ATS) often fail candidates through rigid string matching, while generic LLM solutions suffer from hallucination and opaque scoring. The **AI Career Intelligence Engine** strikes the optimal balance between deterministic precision and semantic intelligence:

- **📄 Robust Resume PDF Extraction**: Powered by PyMuPDF (`fitz`) with strict `%PDF` magic-byte verification and 10MB memory-safe chunked upload streaming.
- **🔍 Dual-Tier Skill Matching**:
  - **Exact Match Baseline**: High-speed set intersection against canonical skill vocabularies and alias dictionaries.
  - **Semantic Matcher**: Context-aware cosine similarity using `sentence-transformers/all-MiniLM-L6-v2` to recognize related technologies (e.g., *PostgreSQL ↔ MySQL*, *PyTorch ↔ Deep Learning*, *GCP ↔ AWS*).
- **📊 100% Interpretable Match Scoring**: Deterministic, weighted heuristic scoring formula with transparent matched, partial, and missing breakdowns.
- **🎯 Prioritized Skill Gap Analysis**: Gaps are ranked by requirement criticality (e.g., detecting keywords like *"must have"*, *"required"*, *"minimum"*) and position prominence within the job posting.
- **💡 Actionable Career Recommendations**: Rule-based recommendations tailored to identified skill gaps—suggesting concrete resume bullet revisions and interview preparation topics.
- **🖥️ Responsive Modern Web UI**: Fast, interactive single-page interface served directly by FastAPI without complex build toolchains.
- **📈 Comprehensive Offline Benchmark Suite**: Includes an evaluated benchmark on labeled skill pairs with precision, recall, macro F1, and threshold sweeps.

---

## 🏛️ System Architecture

The project strictly decouples core machine learning logic from the web server layer. The ML pipeline has **zero dependencies on FastAPI**.

```
┌────────────────────────────────────────────────────────────────────────┐
│                        Web Browser Frontend                            │
│           (Upload PDF + Paste JD Text → Interactive Results)           │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │ HTTP Multipart Form
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│                        FastAPI Adapter (app/)                          │
│         - Validates PDF size (<10MB) & %PDF magic bytes                │
│         - Endpoints: GET /health | POST /analyze | GET /               │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │ In-memory bytes + text
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│                        ML Core Pipeline (ml/)                          │
│                                                                        │
│   Resume PDF ──► PDF Extraction (PyMuPDF) ──► Preprocessing            │
│   JD Text    ───────────────────────────────► Preprocessing            │
│                                                     │                  │
│                                                     ▼                  │
│                                              Skill Extraction          │
│                                       (Canonical Vocab & Aliases)      │
│                                                     │                  │
│                                                     ▼                  │
│                                          Exact Matching Baseline       │
│                                            (Set Intersection)          │
│                                                     │                  │
│                                                     ▼                  │
│                                          Semantic Matching Tier        │
│                                        (MiniLM Cosine Similarity)      │
│                                                     │                  │
│                                                     ▼                  │
│                                          Transparent Match Score       │
│                                                     │                  │
│                                                     ▼                  │
│                                          Prioritized Gap Ranking       │
│                                                     │                  │
│                                                     ▼                  │
│                                          Rule-Based Recommendations    │
└────────────────────────────────────────────────────────────────────────┘
```

### Layer Responsibilities

| Directory / Layer | Responsibility | Nature |
|---|---|---|
| **`frontend/`** | Drag-and-drop PDF upload, progress state, glassmorphism results dashboard | Client-side UI |
| **`app/`** | FastAPI endpoints, Pydantic schemas, file validation, HTTP error handling | API Adapter |
| **`ml/extraction/`** | Extracting raw text from PDF files using PyMuPDF | Deterministic |
| **`ml/preprocessing/`** | Whitespace normalization, unicode sanitization, section parsing | Deterministic |
| **`ml/skills/`** | Curated technical vocabulary, alias expansion, rich skill descriptions | Knowledge / Rule-based |
| **`ml/matching/exact/`** | Exact canonical set intersection baseline | Deterministic Baseline |
| **`ml/matching/semantic/`**| Dense vector embeddings and cosine similarity using MiniLM | Embedding ML |
| **`ml/scoring/`** | Weighted coverage score calculation | Interpretable Heuristic |
| **`ml/gaps/`** | Missing and partial skill ranking based on JD requirement cues | Heuristic Ranking |
| **`ml/recommendations/`** | Resume improvement tips and interview questions generated from gaps | Rule-based Templates |
| **`evaluation/`** | Labeled validation datasets, offline benchmarks, threshold sweeps | Offline Analysis |

---

## ⚙️ How Matching & Scoring Works

### 1. Canonical Skill Extraction
Skills in both the resume and the job description are extracted against a curated technical vocabulary (`ml/skills/vocabulary.py`) and alias mapping (`ml/skills/aliases.py`), normalizing variations like `React.js` → `React`, `k8s` → `Kubernetes`, and `Amazon Web Services` → `AWS`.

### 2. Multi-Tier Matching Engine
1. **Exact Match Baseline**:
   $$\text{Matched}_{\text{exact}} = \text{Skills}_{\text{resume}} \cap \text{Skills}_{\text{JD}}$$
2. **Semantic Similarity Tier**:
   For any remaining JD skills not matched exactly, cosine similarity is computed between their description embeddings and the applicant's skill embeddings using `sentence-transformers/all-MiniLM-L6-v2`:
   - **Semantic Match ($\ge 0.60$)**: High conceptual overlap (e.g., *PostgreSQL* for *MySQL*). Full skill credit with a minor confidence discount.
   - **Partial Match ($0.45 \le \text{sim} < 0.60$)**: Related or adjacent capability (e.g., *Pandas* for *Data Analysis*).
   - **Missing Gap ($< 0.45$)**: Skill identified in JD with no comparable equivalent in the resume.

### 3. Interpretable Match Score Formula

Unlike opaque neural score outputs, the engine computes a transparent, auditable score:

$$\text{Overall Score} = \min\left(100, \; 100 \times \frac{\text{Exact Count} + 0.85 \times \text{Semantic Count} + 0.40 \times \text{Partial Count}}{\text{Total JD Skills}}\right)$$

> **Important Note:** This score is an interpretable matching heuristic for career decision support—it is not an automated hiring decision or an official ATS benchmark.

---

## 📁 Repository Structure

```text
ai-career-intelligence-engine/
├── .github/                     # CI workflows and issue templates
├── .python-version              # Python version pin (3.13) for deployment
├── Procfile                     # Process file for cloud hosts (Render/Heroku)
├── pytest.ini                   # Pytest configuration
├── requirements.txt             # Dependencies with CPU-only PyTorch pin
├── README.md                    # Project documentation
│
├── app/                         # FastAPI Web Application Layer
│   ├── __init__.py
│   ├── main.py                  # API endpoints (/health, /analyze, /)
│   └── schemas.py               # Pydantic input/output schemas
│
├── frontend/                    # Web UI (Served by FastAPI)
│   ├── index.html               # Main dashboard UI
│   ├── styles.css               # Modern CSS styling & glassmorphism
│   ├── app.js                   # Interactive client logic & API client
│   └── assets/                  # Icons and static media
│
├── ml/                          # Core ML & Matching Pipeline (Framework-agnostic)
│   ├── pipeline.py              # End-to-end analysis pipeline
│   ├── extraction/              # PDF parsing (PyMuPDF)
│   ├── preprocessing/           # Text cleaning and normalization
│   ├── skills/                  # Vocabulary, aliases, extraction, and descriptions
│   ├── matching/                # Exact set intersection & semantic vector matching
│   ├── scoring/                 # Weighted coverage scoring heuristic
│   ├── gaps/                    # Skill gap priority ranking
│   └── recommendations/         # Rule-based resume suggestions and interview Qs
│
├── data/                        # Datasets & evaluation assets
│   ├── raw/                     # Sample resumes and raw inputs
│   └── evaluation/              # Ground-truth labeled skill pairs and profiles
│       ├── LABELS.md            # Annotation guideline
│       ├── skill_pairs.json     # Labeled skill pairs (exact, partial, missing)
│       └── score_profiles.json  # Multi-skill profile sanity tests
│
├── evaluation/                  # Offline Evaluation & Metric Runners
│   ├── metrics.py               # Precision, Recall, Macro-F1 computation
│   ├── predictors.py            # Baseline vs Semantic evaluation predictors
│   └── run_eval.py              # Benchmark execution and threshold sweep CLI
│
├── tests/                       # Automated Test Suite
│   ├── api/                     # FastAPI endpoint and validation tests
│   └── unit/                    # Unit tests for matching, scoring, and recommendations
│
├── scripts/                     # Developer & Utility Scripts
│   ├── make_sample_resume.py    # Generates a synthetic test resume PDF
│   └── verify_frontend_handlers.mjs # Frontend handler validator
│
└── docs/                        # Specifications & In-depth Guides
    ├── PROJECT_SPEC.md          # Architectural rules & project goals
    ├── architecture.md          # Detailed architecture & layer breakdowns
    ├── evaluation.md            # Benchmark methodology, metrics & error analysis
    └── deploy.md                # Cloud deployment guide (Render)
```

---

## ⚡ Quick Start & Local Setup

### Prerequisites
- Python **3.11**, **3.12**, or **3.13**
- `git`

### 1. Clone & Set Up Virtual Environment

**Windows (PowerShell):**
```powershell
git clone https://github.com/Swalehaha/ai-career-intelligence-engine.git
cd ai-career-intelligence-engine

python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

**macOS / Linux:**
```bash
git clone https://github.com/Swalehaha/ai-career-intelligence-engine.git
cd ai-career-intelligence-engine

python3 -m venv .venv
source .venv/bin/activate
```

### 2. Install Dependencies
The `requirements.txt` file is pre-configured with a CPU-only PyTorch build to avoid downloading 2GB+ of unnecessary NVIDIA CUDA binaries:

```bash
pip install -r requirements.txt
```

### 3. Generate a Sample Resume (Optional)
To test the pipeline immediately, generate a sample software engineer resume PDF:

```bash
python scripts/make_sample_resume.py
# Outputs to data/raw/sample_resume.pdf
```

### 4. Start the Application

```bash
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Open your browser and navigate to:
👉 **[http://127.0.0.1:8000](http://127.0.0.1:8000)**

---

## 🔌 API Reference

### `GET /health`
Liveness probe that confirms the server is healthy without triggering heavy model loading.

**Response (`200 OK`):**
```json
{
  "status": "ok",
  "service": "ai-career-intelligence-engine"
}
```

---

### `POST /analyze`
Primary inference endpoint. Accepts a resume PDF and job description text via `multipart/form-data`.

**Form Parameters:**
- `resume`: File (`.pdf` only, maximum 10MB)
- `job_description`: String (non-empty)

**Sample Request (cURL):**
```bash
curl -X POST http://127.0.0.1:8000/analyze \
  -F "resume=@data/raw/sample_resume.pdf" \
  -F "job_description=We are seeking a Senior Python Engineer with FastAPI, Docker, and PostgreSQL experience."
```

**Response Schema (`200 OK`):**
```json
{
  "overall_score": 85.0,
  "score_breakdown": {
    "overall_score": 85.0,
    "jd_skill_count": 4,
    "exact_count": 3,
    "semantic_count": 1,
    "partial_count": 0,
    "exact_matched_skills": ["python", "fastapi", "docker"],
    "semantic_matched_skills": [
      {
        "jd_skill": "postgresql",
        "best_resume_skill": "sql",
        "similarity": 0.72
      }
    ],
    "match_thresholds": {
      "semantic_match": 0.60,
      "partial_match": 0.45
    }
  },
  "matched_skills": ["python", "fastapi", "docker"],
  "semantic_matched_skills": [
    {
      "jd_skill": "postgresql",
      "best_resume_skill": "sql",
      "similarity": 0.72
    }
  ],
  "partial_skills": [],
  "missing_skills": [],
  "prioritized_gaps": [],
  "recommendations": {
    "resume_suggestions": [
      "Highlight production achievements and metrics using your matched skills: Python, FastAPI, Docker."
    ],
    "interview_prep_questions": [
      "Explain how you design scalable REST APIs using FastAPI and containerize them with Docker."
    ]
  },
  "resume_skills": ["python", "fastapi", "flask", "docker", "postgresql", "sql", "git", "aws"],
  "jd_skills": ["python", "fastapi", "docker", "postgresql"],
  "resume_text_preview": "Alex Rivera\nSoftware Engineer..."
}
```

---

## 📊 Evaluation & Benchmark Results

Skill matching performance was evaluated using an offline, gold-standard labeled dataset of canonical skill pairs ($n=30$) and sanity score profiles.

To reproduce the benchmark:
```bash
python -m evaluation.run_eval
```

### Benchmark Results ($n=30$)

| System | Label Accuracy | Macro F1 | Exact F1 | Partial F1 | Missing F1 |
|---|:---:|:---:|:---:|:---:|:---:|
| **Baseline (Exact Match Only)** | 50.0% | 0.5152 | **1.0000** | 0.0000 | 0.5455 |
| **Exact + Semantic (`all-MiniLM-L6-v2`)** | **100.0%** | **1.0000** | **1.0000** | **1.0000** | **1.0000** |

### Why Semantic Matching Matters
- **Exact matching alone fails** whenever a candidate lists equivalent or complementary technologies (e.g. *MySQL* vs *PostgreSQL*, *PyTorch* vs *Deep Learning*).
- Under the exact baseline, **15 out of 15** related substitutions are incorrectly classified as completely missing (false negatives).
- Embedding similarity captures conceptual relationships accurately without needing millions of brittle keyword rules.

### Profile Tier Score Calibration
Sanity evaluation across synthetic candidate tiers confirmed expected score separation:
- **Strong Match Profile**: `100.0%`
- **Medium Match Profile**: `66.53%`
- **Weak Match Profile**: `0.0%`

For complete methodology, error analysis, and threshold sweeps, see [docs/evaluation.md](docs/evaluation.md).

---

## ☁️ Deployment (Render / Cloud)

The service is fully stateless (no persistent database required) and ready for one-click deployment on platforms like Render or Heroku.

### Deploying on Render
1. Connect your repository to [Render](https://render.com) and select **Web Service**.
2. **Environment:** `Python 3`
3. **Build Command:**
   ```bash
   pip install -r requirements.txt && python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')"
   ```
   *(Pre-downloads the transformer weights during the build step to eliminate first-request cold starts)*
4. **Start Command:**
   ```bash
   uvicorn app.main:app --host 0.0.0.0 --port $PORT
   ```

### CPU-Only Memory Optimization
- PyTorch is pinned to `torch==2.14.0+cpu` in `requirements.txt`.
- This avoids downloading 2GB+ of NVIDIA CUDA dependencies, keeping the container image lean and running smoothly within memory-constrained environments.

---

## 🧪 Testing & Quality Assurance

The codebase includes comprehensive unit, integration, and API test suites.

```bash
# Run all tests
pytest

# Run tests with verbose output
pytest -v

# Validate frontend event handlers
node scripts/verify_frontend_handlers.mjs
```

**Test Coverage Highlights:**
- `tests/api/test_api.py`: Magic-byte checks, oversized upload rejection, health endpoint, payload verification.
- `tests/unit/test_matching_and_scoring.py`: Exact matching, semantic thresholds, score formula bounds $[0, 100]$.
- `tests/unit/test_recommendations.py`: Gap prioritization and recommendation generation.
- `tests/unit/test_evaluation_metrics.py`: Precision, recall, and macro F1 metric calculations.

---

## 🛡️ Design Guardrails & Philosophy

1. **No Black-Box Scoring**: We do not send resumes to closed-source LLMs to generate arbitrary match percentages. Scoring is calculated through a deterministic, explainable heuristic.
2. **No False ATS Claims**: We do not claim this is an "official ATS clone" or predictor of human hiring decisions. It is designed as an advisory decision-support tool.
3. **Graceful Degradation**: If embeddings fail or are unavailable, the exact-match baseline functions autonomously.
4. **Strict Memory & Safety Bounds**: All uploaded documents are validated for the `%PDF` signature and capped at 10MB to prevent memory exhaustion attacks.

---

## 📄 License

Distributed under the MIT License. See `LICENSE` for more information.
