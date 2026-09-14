"""Predictors for evaluation — wraps production matchers without changing them."""

from __future__ import annotations

from ml.matching.exact import exact_match
from ml.matching.semantic import embed_skills, semantic_match
from ml.scoring.score import compute_score
from sklearn.metrics.pairwise import cosine_similarity


def predict_baseline_pair(resume_skill: str, jd_skill: str) -> tuple[str, float | None]:
    """Exact-only baseline: exact if canonical names match, else missing."""
    result = exact_match([resume_skill], [jd_skill])
    if jd_skill in result["matched"]:
        return "exact", 1.0
    return "missing", None


def predict_semantic_system_pair(
    resume_skill: str,
    jd_skill: str,
    match_threshold: float = 0.60,
    partial_threshold: float = 0.45,
) -> tuple[str, float | None]:
    """Exact + semantic system mapped onto {exact, partial, missing}.

    Mapping:
      - exact canonical match -> exact
      - semantic_matched OR partial bucket -> partial  (related match)
      - still missing -> missing
    """
    exact = exact_match([resume_skill], [jd_skill])
    if jd_skill in exact["matched"]:
        return "exact", 1.0

    semantic = semantic_match(
        [resume_skill],
        [jd_skill],
        match_threshold=match_threshold,
        partial_threshold=partial_threshold,
    )
    detail = semantic["details"][0]
    similarity = detail["similarity"]
    status = detail["status"]

    if status in {"semantic_matched", "partial"}:
        return "partial", similarity
    return "missing", similarity


def pair_similarity(resume_skill: str, jd_skill: str) -> float:
    """Raw cosine similarity between two skill description embeddings."""
    vectors = embed_skills([resume_skill, jd_skill])
    return float(cosine_similarity(vectors[0:1], vectors[1:2])[0, 0])


def predict_profile_scores(
    resume_skills: list[str],
    jd_skills: list[str],
    match_threshold: float = 0.60,
    partial_threshold: float = 0.45,
) -> dict:
    """Score a multi-skill profile under baseline and full systems."""
    exact = exact_match(resume_skills, jd_skills)

    baseline_score = compute_score(
        jd_skill_count=len(jd_skills),
        exact_matched_count=len(exact["matched"]),
        semantic_matched_count=0,
        partial_count=0,
    )

    semantic = semantic_match(
        resume_skills,
        exact["missing"],
        match_threshold=match_threshold,
        partial_threshold=partial_threshold,
    )
    full_score = compute_score(
        jd_skill_count=len(jd_skills),
        exact_matched_count=len(exact["matched"]),
        semantic_matched_count=len(semantic["semantic_matched"]),
        partial_count=len(semantic["partial"]),
    )

    return {
        "exact_matched": exact["matched"],
        "semantic_matched": semantic["semantic_matched"],
        "partial": semantic["partial"],
        "missing": semantic["still_missing"],
        "baseline_score": baseline_score["overall_score"],
        "full_score": full_score["overall_score"],
        "baseline_breakdown": baseline_score["score_breakdown"],
        "full_breakdown": full_score["score_breakdown"],
    }
