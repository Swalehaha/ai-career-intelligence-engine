"""Embedding-based semantic skill matching.

Uses sentence-transformers (all-MiniLM-L6-v2). This is the ML improvement
over the exact-match baseline — not an LLM scoring engine.
"""

from __future__ import annotations

from functools import lru_cache

import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

from ml.skills.descriptions import describe_skill

# Thresholds tuned for short skill description embeddings
MATCH_THRESHOLD = 0.60
PARTIAL_THRESHOLD = 0.45
MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"


@lru_cache(maxsize=1)
def get_embedding_model():
    """Lazy-load the embedding model once per process."""
    from sentence_transformers import SentenceTransformer

    return SentenceTransformer(MODEL_NAME)


def embed_skills(skills: list[str]) -> np.ndarray:
    """Return L2-normalized embeddings for skill strings."""
    if not skills:
        return np.zeros((0, 384), dtype=np.float32)
    model = get_embedding_model()
    phrases = [describe_skill(skill) for skill in skills]
    vectors = model.encode(phrases, normalize_embeddings=True)
    return np.asarray(vectors, dtype=np.float32)


def semantic_match(
    resume_skills: list[str],
    unmatched_jd_skills: list[str],
    match_threshold: float = MATCH_THRESHOLD,
    partial_threshold: float = PARTIAL_THRESHOLD,
) -> dict:
    """Match remaining JD skills to resume skills via cosine similarity.

    Returns semantic matches / partials and still-missing skills.
    """
    if not unmatched_jd_skills:
        return {
            "semantic_matched": [],
            "partial": [],
            "still_missing": [],
            "details": [],
        }

    if not resume_skills:
        return {
            "semantic_matched": [],
            "partial": [],
            "still_missing": list(unmatched_jd_skills),
            "details": [
                {
                    "jd_skill": skill,
                    "best_resume_skill": None,
                    "similarity": 0.0,
                    "status": "missing",
                }
                for skill in unmatched_jd_skills
            ],
        }

    resume_vecs = embed_skills(resume_skills)
    jd_vecs = embed_skills(unmatched_jd_skills)
    sim_matrix = cosine_similarity(jd_vecs, resume_vecs)

    semantic_matched: list[dict] = []
    partial: list[dict] = []
    still_missing: list[str] = []
    details: list[dict] = []

    for i, jd_skill in enumerate(unmatched_jd_skills):
        best_j = int(np.argmax(sim_matrix[i]))
        score = float(sim_matrix[i, best_j])
        best_resume = resume_skills[best_j]

        if score >= match_threshold:
            status = "semantic_matched"
            item = {
                "jd_skill": jd_skill,
                "resume_skill": best_resume,
                "similarity": round(score, 4),
            }
            semantic_matched.append(item)
        elif score >= partial_threshold:
            status = "partial"
            item = {
                "jd_skill": jd_skill,
                "resume_skill": best_resume,
                "similarity": round(score, 4),
            }
            partial.append(item)
        else:
            status = "missing"
            still_missing.append(jd_skill)
            item = {
                "jd_skill": jd_skill,
                "resume_skill": best_resume,
                "similarity": round(score, 4),
            }

        details.append(
            {
                "jd_skill": jd_skill,
                "best_resume_skill": best_resume,
                "similarity": round(score, 4),
                "status": status,
            }
        )

    return {
        "semantic_matched": semantic_matched,
        "partial": partial,
        "still_missing": still_missing,
        "details": details,
    }
