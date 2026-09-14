"""Rule-based resume tips and interview questions.

This module is NOT part of match scoring. It generates deterministic
template suggestions from prioritized gaps and match buckets.
No LLM is used here.
"""

from __future__ import annotations

MAX_RESUME_TIPS = 5
MAX_INTERVIEW_QUESTIONS = 5


def build_recommendations(
    prioritized_gaps: list[dict],
    matched_skills: list[str],
    partial_skills: list[dict],
    overall_score: float,
) -> dict:
    """Return resume tips and interview questions from analysis outputs."""
    resume_suggestions = _resume_suggestions(
        prioritized_gaps, matched_skills, partial_skills, overall_score
    )
    interview_questions = _interview_questions(prioritized_gaps, partial_skills)

    return {
        "method": "rule_based_templates",
        "note": (
            "Suggestions are deterministic templates derived from skill gaps. "
            "They are not LLM-generated and do not affect the match score."
        ),
        "resume_suggestions": resume_suggestions,
        "interview_questions": interview_questions,
    }


def _resume_suggestions(
    prioritized_gaps: list[dict],
    matched_skills: list[str],
    partial_skills: list[dict],
    overall_score: float,
) -> list[dict]:
    tips: list[dict] = []

    for gap in prioritized_gaps:
        if len(tips) >= MAX_RESUME_TIPS:
            break
        skill = gap["skill"]
        if gap.get("status") == "missing":
            tips.append(
                {
                    "skill": skill,
                    "priority": gap.get("rank"),
                    "suggestion": (
                        f"If you have {skill} experience, add a concrete bullet under "
                        f"Skills or Experience (tool, scope, and outcome). If not, "
                        f"consider a small portfolio project that demonstrates {skill}."
                    ),
                }
            )
        elif gap.get("status") == "partial":
            related = gap.get("similar_resume_skill") or "a related skill"
            tips.append(
                {
                    "skill": skill,
                    "priority": gap.get("rank"),
                    "suggestion": (
                        f"The JD asks for {skill}; your resume is closer to {related}. "
                        f"Clarify transferability in one bullet (e.g. migrated from "
                        f"{related} to {skill}, or comparable responsibilities)."
                    ),
                }
            )

    if matched_skills and len(tips) < MAX_RESUME_TIPS:
        highlight = ", ".join(matched_skills[:3])
        tips.append(
            {
                "skill": None,
                "priority": None,
                "suggestion": (
                    f"Lead with strong overlaps early in the resume summary: {highlight}."
                ),
            }
        )

    if overall_score < 40 and len(tips) < MAX_RESUME_TIPS:
        tips.append(
            {
                "skill": None,
                "priority": None,
                "suggestion": (
                    "Overall coverage is low for this JD. Prioritize roles that match "
                    "your strongest skills, or tailor a targeted resume version for "
                    "this posting's required stack."
                ),
            }
        )

    if not tips:
        tips.append(
            {
                "skill": None,
                "priority": None,
                "suggestion": (
                    "Coverage looks strong. Quantify impact on matched skills "
                    "(latency, accuracy, users, revenue) to strengthen the narrative."
                ),
            }
        )

    return tips[:MAX_RESUME_TIPS]


def _interview_questions(
    prioritized_gaps: list[dict],
    partial_skills: list[dict],
) -> list[dict]:
    questions: list[dict] = []

    for gap in prioritized_gaps:
        if len(questions) >= MAX_INTERVIEW_QUESTIONS:
            break
        skill = gap["skill"]
        if gap.get("status") == "missing":
            questions.append(
                {
                    "skill": skill,
                    "question": (
                        f"Walk me through a project where you would apply {skill}. "
                        f"What trade-offs would you consider?"
                    ),
                    "intent": "Probe depth on a missing JD requirement",
                }
            )
        else:
            related = gap.get("similar_resume_skill") or "related tools"
            questions.append(
                {
                    "skill": skill,
                    "question": (
                        f"You list experience close to {related}. How would you ramp "
                        f"up on {skill}, and what transfers directly?"
                    ),
                    "intent": "Test transfer from a partial/related skill",
                }
            )

    if not questions and partial_skills:
        item = partial_skills[0]
        questions.append(
            {
                "skill": item.get("jd_skill"),
                "question": (
                    f"Compare {item.get('resume_skill')} and {item.get('jd_skill')}: "
                    f"when would you choose each?"
                ),
                "intent": "Differentiate related technologies",
            }
        )

    if not questions:
        questions.append(
            {
                "skill": None,
                "question": (
                    "Which requirement in this job description aligns best with your "
                    "strongest project, and how would you prove impact in 2 minutes?"
                ),
                "intent": "General behavioral + technical storytelling",
            }
        )

    return questions[:MAX_INTERVIEW_QUESTIONS]
