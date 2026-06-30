"""Pydantic schemas for structured analysis output."""

from __future__ import annotations

from pathlib import PurePosixPath, PureWindowsPath
from typing import Literal

from pydantic import BaseModel, Field, field_validator


class EvidenceItem(BaseModel):
    """Evidence supporting a finding or recommendation."""

    file_path: str | None = None
    line: int | None = None
    command: str | None = None
    summary: str = ""
    raw_excerpt: str | None = None

    @field_validator("file_path")
    @classmethod
    def validate_relative_file_path(cls, value: str | None) -> str | None:
        """Keep report evidence paths portable and project-relative."""
        if value is not None and _is_absolute_path(value):
            raise ValueError("file_path must be relative to the project root.")
        return value


class Finding(BaseModel):
    """A concrete observation about the repository."""

    title: str
    severity: Literal["info", "low", "medium", "high", "critical"] = "info"
    category: str = "general"
    description: str = ""
    evidence: list[EvidenceItem] = Field(default_factory=list)
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)


class Recommendation(BaseModel):
    """A suggested follow-up action."""

    title: str
    priority: Literal["low", "medium", "high"] = "medium"
    description: str = ""
    suggested_steps: list[str] = Field(default_factory=list)
    related_findings: list[str] = Field(default_factory=list)


class ProjectSummary(BaseModel):
    """High-level project profile summary."""

    project_types: list[str] = Field(default_factory=list)
    languages: list[str] = Field(default_factory=list)
    frameworks: list[str] = Field(default_factory=list)
    package_managers: list[str] = Field(default_factory=list)
    entry_points: list[str] = Field(default_factory=list)
    key_config_files: list[str] = Field(default_factory=list)

    @field_validator("entry_points", "key_config_files")
    @classmethod
    def validate_relative_paths(cls, values: list[str]) -> list[str]:
        """Keep project summary paths portable and project-relative."""
        for value in values:
            if _is_absolute_path(value):
                raise ValueError("project summary paths must be relative to the project root.")
        return values


class AnalysisReport(BaseModel):
    """Structured report produced by RepoInsight Agent."""

    title: str = "RepoInsight Analysis Report"
    task: str = ""
    generated_by: str = "RepoInsight Agent"
    project_summary: ProjectSummary = Field(default_factory=ProjectSummary)
    executive_summary: str = ""
    findings: list[Finding] = Field(default_factory=list)
    recommendations: list[Recommendation] = Field(default_factory=list)
    evidence_files: list[str] = Field(default_factory=list)
    limitations: list[str] = Field(default_factory=list)
    next_steps: list[str] = Field(default_factory=list)

    @field_validator("evidence_files")
    @classmethod
    def validate_evidence_files(cls, values: list[str]) -> list[str]:
        """Keep report evidence files portable and project-relative."""
        for value in values:
            if _is_absolute_path(value):
                raise ValueError("evidence_files must be relative to the project root.")
        return values


def _is_absolute_path(value: str) -> bool:
    return PureWindowsPath(value).is_absolute() or PurePosixPath(value).is_absolute()
