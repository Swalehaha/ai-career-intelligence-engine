"""Lightweight text preprocessing for resumes and job descriptions."""

from __future__ import annotations

import re

_WHITESPACE_RE = re.compile(r"[ \t]+")
_MULTI_NEWLINE_RE = re.compile(r"\n{3,}")
_BULLET_RE = re.compile(r"[•●○◦▪▸►]\s*")


def preprocess_text(text: str) -> str:
    """Normalize whitespace, bullets, and casing-insensitive noise."""
    if not text:
        return ""

    cleaned = text.replace("\r\n", "\n").replace("\r", "\n")
    cleaned = cleaned.replace("\x00", " ")
    cleaned = _BULLET_RE.sub("- ", cleaned)
    cleaned = _WHITESPACE_RE.sub(" ", cleaned)
    cleaned = _MULTI_NEWLINE_RE.sub("\n\n", cleaned)
    return cleaned.strip()


def split_sections(text: str) -> dict[str, str]:
    """Best-effort section split using common resume/JD headers."""
    headers = [
        "skills",
        "technical skills",
        "experience",
        "work experience",
        "education",
        "projects",
        "summary",
        "requirements",
        "qualifications",
        "responsibilities",
        "preferred qualifications",
        "required skills",
    ]
    pattern = re.compile(
        rf"(?im)^(?:{'|'.join(re.escape(h) for h in headers)})\s*:?\s*$"
    )
    matches = list(pattern.finditer(text))
    if not matches:
        return {"body": text}

    sections: dict[str, str] = {}
    if matches[0].start() > 0:
        sections["preamble"] = text[: matches[0].start()].strip()

    for i, match in enumerate(matches):
        name = match.group(0).strip().rstrip(":").lower()
        start = match.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        sections[name] = text[start:end].strip()
    return sections
