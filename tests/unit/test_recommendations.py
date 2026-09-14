"""Tests for rule-based recommendations (not part of scoring)."""

from __future__ import annotations

from ml.recommendations import build_recommendations


def test_recommendations_from_missing_gaps():
    gaps = [
        {
            "skill": "Kubernetes",
            "status": "missing",
            "rank": 1,
            "similar_resume_skill": None,
        }
    ]
    result = build_recommendations(
        prioritized_gaps=gaps,
        matched_skills=["Python"],
        partial_skills=[],
        overall_score=50.0,
    )
    assert result["method"] == "rule_based_templates"
    assert any("Kubernetes" in (t.get("suggestion") or "") for t in result["resume_suggestions"])
    assert any(q.get("skill") == "Kubernetes" for q in result["interview_questions"])


def test_recommendations_do_not_require_llm_fields():
    result = build_recommendations([], ["Python"], [], 90.0)
    assert "resume_suggestions" in result
    assert "interview_questions" in result
    assert "llm" not in result["method"]
