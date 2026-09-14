"""Create a sample resume PDF for local demos."""

from __future__ import annotations

from pathlib import Path

import pymupdf

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "data" / "raw" / "sample_resume.pdf"

TEXT = """Alex Rivera
Software Engineer | alex.rivera@email.com

SUMMARY
Backend-focused engineer with experience in Python web APIs, data pipelines,
and applied machine learning prototypes.

SKILLS
Python, FastAPI, Flask, Docker, PostgreSQL, SQL, Git, AWS, REST APIs,
Pandas, NumPy, scikit-learn, PyTorch, NLP, CI/CD

EXPERIENCE
Software Engineer — Example Corp (2022–Present)
- Built FastAPI microservices and REST APIs used by internal tools.
- Containerized services with Docker and deployed on AWS.
- Prototyped NLP classifiers with PyTorch and scikit-learn.
- Wrote SQL against PostgreSQL and automated ETL-style jobs.

EDUCATION
B.S. Computer Science
"""


def main() -> None:
    OUT.parent.mkdir(parents=True, exist_ok=True)
    doc = pymupdf.open()
    page = doc.new_page()
    # insert_textbox handles wrapping better for demo content
    page.insert_textbox(
        pymupdf.Rect(50, 50, 545, 792),
        TEXT,
        fontsize=11,
        fontname="helv",
        align=0,
    )
    doc.save(OUT)
    doc.close()
    print(f"Wrote {OUT}")


if __name__ == "__main__":
    main()
