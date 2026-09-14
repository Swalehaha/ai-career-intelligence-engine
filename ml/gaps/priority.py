"""Skill-gap prioritization."""

from __future__ import annotations

import re


def prioritize_gaps(
    missing_skills: list[str],
    partial_skills: list[dict],
    jd_text: str,
) -> list[dict]:
    """Rank gaps by simple JD importance signals.

    Priority score combines:
      - missing vs partial (missing ranked higher)
      - earlier first mention in the JD
      - appearance near requirement-like language
    """
    lowered = jd_text.lower()
    gaps: list[dict] = []

    for skill in missing_skills:
        gaps.append(
            _gap_entry(
                skill=skill,
                status="missing",
                jd_text_lower=lowered,
                similarity=None,
                resume_skill=None,
            )
        )

    for item in partial_skills:
        gaps.append(
            _gap_entry(
                skill=item["jd_skill"],
                status="partial",
                jd_text_lower=lowered,
                similarity=item.get("similarity"),
                resume_skill=item.get("resume_skill"),
            )
        )

    gaps.sort(key=lambda g: g["priority_score"], reverse=True)
    for rank, gap in enumerate(gaps, start=1):
        gap["rank"] = rank
    return gaps


def _gap_entry(
    skill: str,
    status: str,
    jd_text_lower: str,
    similarity: float | None,
    resume_skill: str | None,
) -> dict:
    pos = jd_text_lower.find(skill.lower())
    # Earlier mention => higher position score
    if pos < 0:
        position_score = 0.3
    else:
        position_score = 1.0 - (pos / max(len(jd_text_lower), 1))

    requirement_bonus = 0.0
    window = _context_window(jd_text_lower, skill.lower())
    if re.search(r"requir|must have|mandatory|needed|necessary", window):
        requirement_bonus = 0.25

    status_weight = 1.0 if status == "missing" else 0.55
    priority = round(status_weight * (0.75 * position_score + 0.25) + requirement_bonus, 4)

    reason_parts = []
    if status == "missing":
        reason_parts.append("Not found on resume (exact or semantic).")
    else:
        reason_parts.append(
            f"Only partial semantic overlap with '{resume_skill}' "
            f"(similarity={similarity})."
        )
    if requirement_bonus:
        reason_parts.append("Appears near requirement language in the JD.")
    if pos >= 0 and position_score > 0.7:
        reason_parts.append("Mentioned early in the JD.")

    return {
        "skill": skill,
        "status": status,
        "priority_score": priority,
        "reason": " ".join(reason_parts),
        "similar_resume_skill": resume_skill,
        "similarity": similarity,
    }


def _context_window(text: str, skill: str, radius: int = 80) -> str:
    idx = text.find(skill)
    if idx < 0:
        return ""
    start = max(0, idx - radius)
    end = min(len(text), idx + len(skill) + radius)
    return text[start:end]
