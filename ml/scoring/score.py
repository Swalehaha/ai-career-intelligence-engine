"""Interpretable match scoring."""

from __future__ import annotations


def compute_score(
    jd_skill_count: int,
    exact_matched_count: int,
    semantic_matched_count: int,
    partial_count: int,
) -> dict:
    """Compute an explainable 0–100 score from match buckets.

    Buckets are mutually exclusive (exact first, then semantic on the rest).

    Formula:
      credit = exact + 0.85 * semantic + 0.40 * partial
      overall = 100 * credit / jd_skill_count

    Exact matches get full credit. Semantic near-matches get 85%.
    Partials get 40%. A perfect exact match against all JD skills = 100.
    """
    formula = (
        "100 * (exact + 0.85 * semantic + 0.40 * partial) / jd_skill_count"
    )

    if jd_skill_count <= 0:
        return {
            "overall_score": 0.0,
            "score_breakdown": {
                "jd_skill_count": 0,
                "exact_matched_count": 0,
                "semantic_matched_count": 0,
                "partial_count": 0,
                "exact_coverage": 0.0,
                "semantic_coverage": 0.0,
                "partial_coverage": 0.0,
                "credit_weights": {"exact": 1.0, "semantic": 0.85, "partial": 0.40},
                "formula": formula,
            },
        }

    credit = (
        exact_matched_count
        + 0.85 * semantic_matched_count
        + 0.40 * partial_count
    )
    overall = 100.0 * credit / jd_skill_count
    overall = round(min(max(overall, 0.0), 100.0), 2)

    return {
        "overall_score": overall,
        "score_breakdown": {
            "jd_skill_count": jd_skill_count,
            "exact_matched_count": exact_matched_count,
            "semantic_matched_count": semantic_matched_count,
            "partial_count": partial_count,
            "exact_coverage": round(exact_matched_count / jd_skill_count, 4),
            "semantic_coverage": round(semantic_matched_count / jd_skill_count, 4),
            "partial_coverage": round(partial_count / jd_skill_count, 4),
            "credit_weights": {"exact": 1.0, "semantic": 0.85, "partial": 0.40},
            "formula": formula,
        },
    }
