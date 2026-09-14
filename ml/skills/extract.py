"""Skill normalization and extraction against the curated vocabulary."""

from __future__ import annotations

import re

from ml.skills.vocabulary import ALIAS_TO_CANONICAL, ALIASES_BY_LENGTH


def normalize_skill(raw: str) -> str | None:
    """Map a raw skill string to a canonical vocabulary skill, if known."""
    key = " ".join(raw.lower().strip().split())
    if not key:
        return None
    return ALIAS_TO_CANONICAL.get(key)


def extract_skills(text: str) -> list[str]:
    """Extract canonical skills mentioned in text via alias phrase matching.

    Longer aliases are matched first. Word boundaries reduce partial-token noise
    (e.g. avoiding 'java' inside 'javascript' is handled by checking aliases
    ordered by length and consuming matched spans).
    """
    if not text:
        return []

    lowered = text.lower()
    occupied = [False] * len(lowered)
    found: list[str] = []
    seen: set[str] = set()

    for alias in ALIASES_BY_LENGTH:
        pattern = re.compile(rf"(?<![a-z0-9]){re.escape(alias)}(?![a-z0-9])")
        for match in pattern.finditer(lowered):
            start, end = match.span()
            if any(occupied[start:end]):
                continue
            canonical = ALIAS_TO_CANONICAL[alias]
            for i in range(start, end):
                occupied[i] = True
            if canonical not in seen:
                seen.add(canonical)
                found.append(canonical)

    return found
