"""Pydantic schemas for structured analysis output."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class Finding(BaseModel):
    """A concrete observation about the repository."""

    title: str
    summary: str
    severity: Literal["info", "low", "medium", "high"] = "info"
    evidence_file: str | None = None


class Recommendation(BaseModel):
    """A suggested follow-up action."""

    title: str
    rationale: str
    priority: Literal["low", "medium", "high"] = "medium"


class AnalysisReport(BaseModel):
    """Structured report produced by the future Agent runtime."""

    project_path: str
    goal: str
    summary: str
    findings: list[Finding] = Field(default_factory=list)
    recommendations: list[Recommendation] = Field(default_factory=list)
