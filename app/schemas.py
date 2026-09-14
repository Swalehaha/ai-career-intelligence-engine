"""Pydantic response/request schemas for the API."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    status: str = "ok"
    service: str = "ai-career-intelligence-engine"


class AnalyzeResponse(BaseModel):
    overall_score: float
    score_breakdown: dict[str, Any]
    matched_skills: list[str]
    semantic_matched_skills: list[dict[str, Any]] = Field(default_factory=list)
    partial_skills: list[dict[str, Any]]
    missing_skills: list[str]
    prioritized_gaps: list[dict[str, Any]]
    recommendations: dict[str, Any] = Field(default_factory=dict)
    resume_skills: list[str] = Field(default_factory=list)
    jd_skills: list[str] = Field(default_factory=list)
    resume_text_preview: str | None = None
