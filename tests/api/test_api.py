"""API smoke and production-readiness tests."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pymupdf
import pytest
from fastapi.testclient import TestClient

from app.main import MAX_UPLOAD_BYTES, app

client = TestClient(app)


def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "ok"


def _make_resume_pdf(path: Path) -> Path:
    doc = pymupdf.open()
    page = doc.new_page()
    page.insert_text(
        (50, 72),
        (
            "Jane Doe\n"
            "Skills: Python, FastAPI, Docker, PostgreSQL, Git\n"
            "Experience building REST APIs and machine learning prototypes with PyTorch.\n"
        ),
        fontsize=11,
    )
    doc.save(path)
    doc.close()
    return path


@pytest.fixture(scope="module")
def sample_pdf(tmp_path_factory) -> Path:
    folder = tmp_path_factory.mktemp("pdfs")
    return _make_resume_pdf(folder / "resume.pdf")


def test_analyze_response_structure(sample_pdf: Path):
    jd = (
        "We need a backend engineer with Python, FastAPI, Kubernetes, "
        "Docker, and PostgreSQL. Experience with NLP is a plus."
    )
    with sample_pdf.open("rb") as handle:
        response = client.post(
            "/analyze",
            files={"resume": ("resume.pdf", handle, "application/pdf")},
            data={"job_description": jd},
        )

    assert response.status_code == 200, response.text
    payload = response.json()

    for key in [
        "overall_score",
        "score_breakdown",
        "matched_skills",
        "partial_skills",
        "missing_skills",
        "prioritized_gaps",
        "recommendations",
    ]:
        assert key in payload

    assert isinstance(payload["overall_score"], (int, float))
    assert isinstance(payload["matched_skills"], list)
    assert isinstance(payload["missing_skills"], list)
    assert isinstance(payload["prioritized_gaps"], list)
    assert "Python" in payload["matched_skills"]
    assert "FastAPI" in payload["matched_skills"]
    assert payload["recommendations"]["method"] == "rule_based_templates"
    assert payload["recommendations"]["resume_suggestions"]
    assert payload["recommendations"]["interview_questions"]


def test_reject_oversized_upload():
    oversized = b"%PDF-1.4\n" + (b"x" * (MAX_UPLOAD_BYTES + 1))
    response = client.post(
        "/analyze",
        files={"resume": ("big.pdf", oversized, "application/pdf")},
        data={"job_description": "Requires Python and FastAPI."},
    )
    assert response.status_code == 413
    assert "maximum upload size" in response.json()["detail"].lower()


def test_reject_invalid_pdf_bytes_with_pdf_filename():
    response = client.post(
        "/analyze",
        files={"resume": ("fake.pdf", b"not-a-real-pdf-file", "application/pdf")},
        data={"job_description": "Requires Python and FastAPI."},
    )
    assert response.status_code == 400
    assert "valid pdf" in response.json()["detail"].lower()


def test_unexpected_error_hides_internal_details(sample_pdf: Path):
    with sample_pdf.open("rb") as handle:
        with patch(
            "app.main.analyze_resume_against_jd",
            side_effect=RuntimeError("secret torch path /opt/conda/lib/hidden"),
        ):
            response = client.post(
                "/analyze",
                files={"resume": ("resume.pdf", handle, "application/pdf")},
                data={"job_description": "Requires Python."},
            )

    assert response.status_code == 500
    detail = response.json()["detail"]
    assert detail == "Analysis failed due to an internal error."
    assert "secret" not in detail
    assert "torch" not in detail.lower()
    assert "/opt/" not in detail
