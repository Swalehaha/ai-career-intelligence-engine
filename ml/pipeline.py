"""End-to-end career intelligence pipeline (framework-agnostic)."""

from __future__ import annotations

from pathlib import Path

from ml.extraction.pdf import extract_text_from_pdf
from ml.gaps.priority import prioritize_gaps
from ml.matching.exact import exact_match
from ml.matching.semantic import semantic_match
from ml.preprocessing.text import preprocess_text
from ml.recommendations import build_recommendations
from ml.scoring.score import compute_score
from ml.skills.extract import extract_skills


def analyze_resume_against_jd(
    resume_pdf: str | Path | bytes,
    job_description: str,
) -> dict:
    """Run extraction → matching → scoring → gap ranking.

    Returns a structured result suitable for API serialization.
    """
    if not job_description or not str(job_description).strip():
        raise ValueError("job_description must be non-empty")

    resume_raw = extract_text_from_pdf(resume_pdf)
    if not resume_raw.strip():
        raise ValueError("Could not extract text from the resume PDF")

    resume_text = preprocess_text(resume_raw)
    jd_text = preprocess_text(job_description)

    resume_skills = extract_skills(resume_text)
    jd_skills = extract_skills(jd_text)

    exact = exact_match(resume_skills, jd_skills)
    semantic = semantic_match(resume_skills, exact["missing"])

    matched_skills = list(exact["matched"])
    semantic_matched_skills = [m["jd_skill"] for m in semantic["semantic_matched"]]
    partial_skills = semantic["partial"]
    missing_skills = semantic["still_missing"]

    score = compute_score(
        jd_skill_count=len(jd_skills),
        exact_matched_count=len(exact["matched"]),
        semantic_matched_count=len(semantic_matched_skills),
        partial_count=len(partial_skills),
    )

    prioritized_gaps = prioritize_gaps(missing_skills, partial_skills, jd_text)
    recommendations = build_recommendations(
        prioritized_gaps=prioritized_gaps,
        matched_skills=matched_skills,
        partial_skills=partial_skills,
        overall_score=score["overall_score"],
    )

    return {
        "overall_score": score["overall_score"],
        "score_breakdown": {
            **score["score_breakdown"],
            "exact_matched_skills": exact["matched"],
            "semantic_matched_skills": semantic["semantic_matched"],
            "match_thresholds": {
                "semantic_match": 0.60,
                "partial_match": 0.45,
            },
        },
        "matched_skills": matched_skills,
        "semantic_matched_skills": semantic["semantic_matched"],
        "partial_skills": partial_skills,
        "missing_skills": missing_skills,
        "prioritized_gaps": prioritized_gaps,
        "recommendations": recommendations,
        "resume_skills": resume_skills,
        "jd_skills": jd_skills,
        "resume_text_preview": resume_text[:500],
    }


def analyze_texts(resume_text: str, job_description: str) -> dict:
    """Pipeline entry for tests that skip PDF extraction."""
    resume_text = preprocess_text(resume_text)
    jd_text = preprocess_text(job_description)

    resume_skills = extract_skills(resume_text)
    jd_skills = extract_skills(jd_text)

    exact = exact_match(resume_skills, jd_skills)
    semantic = semantic_match(resume_skills, exact["missing"])

    score = compute_score(
        jd_skill_count=len(jd_skills),
        exact_matched_count=len(exact["matched"]),
        semantic_matched_count=len(semantic["semantic_matched"]),
        partial_count=len(semantic["partial"]),
    )
    prioritized_gaps = prioritize_gaps(
        semantic["still_missing"], semantic["partial"], jd_text
    )
    recommendations = build_recommendations(
        prioritized_gaps=prioritized_gaps,
        matched_skills=exact["matched"],
        partial_skills=semantic["partial"],
        overall_score=score["overall_score"],
    )

    return {
        "overall_score": score["overall_score"],
        "score_breakdown": score["score_breakdown"],
        "matched_skills": exact["matched"],
        "semantic_matched_skills": semantic["semantic_matched"],
        "partial_skills": semantic["partial"],
        "missing_skills": semantic["still_missing"],
        "prioritized_gaps": prioritized_gaps,
        "recommendations": recommendations,
        "resume_skills": resume_skills,
        "jd_skills": jd_skills,
    }
