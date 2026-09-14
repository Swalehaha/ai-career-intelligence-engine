"""PDF text extraction via PyMuPDF."""

from __future__ import annotations

from pathlib import Path

import pymupdf


def extract_text_from_pdf(source: str | Path | bytes) -> str:
    """Extract plain text from a PDF file path or raw bytes."""
    if isinstance(source, (str, Path)):
        doc = pymupdf.open(source)
    else:
        doc = pymupdf.open(stream=source, filetype="pdf")

    try:
        parts: list[str] = []
        for page in doc:
            parts.append(page.get_text("text"))
        return "\n".join(parts).strip()
    finally:
        doc.close()
