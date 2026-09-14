"""Exact skill-set matching baseline."""

from __future__ import annotations


def exact_match(resume_skills: list[str], jd_skills: list[str]) -> dict:
    """Return exact overlap between resume and JD canonical skill sets."""
    resume_set = set(resume_skills)
    jd_set = set(jd_skills)

    matched = sorted(resume_set & jd_set)
    missing = sorted(jd_set - resume_set)
    extra = sorted(resume_set - jd_set)

    coverage = (len(matched) / len(jd_set)) if jd_set else 0.0

    return {
        "matched": matched,
        "missing": missing,
        "extra_resume_skills": extra,
        "exact_coverage": round(coverage, 4),
    }
