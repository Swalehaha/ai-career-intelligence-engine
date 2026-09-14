"""FastAPI application — thin adapter over the ML pipeline."""

from __future__ import annotations

import logging
from pathlib import Path

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.schemas import AnalyzeResponse, HealthResponse
from ml.pipeline import analyze_resume_against_jd

logger = logging.getLogger(__name__)

ROOT = Path(__file__).resolve().parent.parent
FRONTEND_DIR = ROOT / "frontend"

# Reject oversized PDFs before parsing (in-memory upload path).
MAX_UPLOAD_BYTES = 10 * 1024 * 1024  # 10 MB

app = FastAPI(
    title="AI Career Intelligence Engine",
    description="Match resume skills to job descriptions with exact + semantic analysis.",
    version="0.1.0",
)

# No CORS middleware: the UI is served by this same app and calls /analyze
# with a relative URL (same-origin). Open CORS is unnecessary.


@app.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse()


def _is_pdf_bytes(data: bytes) -> bool:
    """Lightweight magic-byte check for PDF files."""
    return data.startswith(b"%PDF")


async def _read_upload_with_limit(upload: UploadFile, max_bytes: int) -> bytes:
    """Read an upload in chunks; reject before exceeding max_bytes."""
    chunks: list[bytes] = []
    total = 0
    chunk_size = 1024 * 1024  # 1 MB
    while True:
        chunk = await upload.read(chunk_size)
        if not chunk:
            break
        total += len(chunk)
        if total > max_bytes:
            raise HTTPException(
                status_code=413,
                detail=(
                    f"Resume PDF exceeds the maximum upload size of "
                    f"{max_bytes // (1024 * 1024)} MB."
                ),
            )
        chunks.append(chunk)
    return b"".join(chunks)


@app.post("/analyze", response_model=AnalyzeResponse)
async def analyze(
    resume: UploadFile = File(..., description="Resume PDF"),
    job_description: str = Form(..., description="Job description text"),
) -> AnalyzeResponse:
    if not resume.filename or not resume.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Resume must be a PDF file.")

    if not job_description.strip():
        raise HTTPException(status_code=400, detail="job_description must be non-empty.")

    pdf_bytes = await _read_upload_with_limit(resume, MAX_UPLOAD_BYTES)
    if not pdf_bytes:
        raise HTTPException(status_code=400, detail="Uploaded PDF is empty.")

    if not _is_pdf_bytes(pdf_bytes):
        raise HTTPException(
            status_code=400,
            detail="Resume must be a valid PDF file.",
        )

    try:
        result = analyze_resume_against_jd(pdf_bytes, job_description)
    except ValueError as exc:
        # Intentional client-facing validation from the pipeline
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception:
        logger.exception("Unexpected failure during /analyze")
        raise HTTPException(
            status_code=500,
            detail="Analysis failed due to an internal error.",
        ) from None

    return AnalyzeResponse(**result)


@app.get("/")
def index() -> FileResponse:
    index_path = FRONTEND_DIR / "index.html"
    if not index_path.exists():
        raise HTTPException(status_code=404, detail="Frontend not found.")
    return FileResponse(index_path)


if FRONTEND_DIR.exists():
    app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")
