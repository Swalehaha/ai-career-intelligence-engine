"""Unit tests for normalization, exact matching, and scoring."""

from __future__ import annotations

from ml.matching.exact import exact_match
from ml.scoring.score import compute_score
from ml.skills.extract import extract_skills, normalize_skill


def test_normalize_skill_aliases():
    assert normalize_skill("python3") == "Python"
    assert normalize_skill("JS") == "JavaScript"
    assert normalize_skill("scikit learn") == "scikit-learn"
    assert normalize_skill("unknown-skill-xyz") is None


def test_extract_skills_from_text():
    text = (
        "Experienced in Python, FastAPI, and Docker. "
        "Built NLP pipelines with PyTorch."
    )
    skills = extract_skills(text)
    assert "Python" in skills
    assert "FastAPI" in skills
    assert "Docker" in skills
    assert "Natural Language Processing" in skills or "PyTorch" in skills


def test_exact_match_baseline():
    resume = ["Python", "Docker", "SQL"]
    jd = ["Python", "Kubernetes", "SQL"]
    result = exact_match(resume, jd)
    assert result["matched"] == ["Python", "SQL"]
    assert result["missing"] == ["Kubernetes"]
    assert result["exact_coverage"] == round(2 / 3, 4)


def test_compute_score_weights():
    result = compute_score(
        jd_skill_count=10,
        exact_matched_count=5,
        semantic_matched_count=2,
        partial_count=1,
    )
    # 100 * (5 + 0.85*2 + 0.40*1) / 10 = 100 * 7.1 / 10 = 71.0
    assert result["overall_score"] == 71.0
    assert result["score_breakdown"]["credit_weights"]["exact"] == 1.0


def test_compute_score_empty_jd():
    result = compute_score(0, 0, 0, 0)
    assert result["overall_score"] == 0.0
