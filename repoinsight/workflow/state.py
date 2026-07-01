"""Workflow state definitions."""

from __future__ import annotations

import operator
from typing import Annotated, Any, TypedDict


class RepoInsightState(TypedDict):
    """State passed between LangGraph workflow nodes."""

    project_root: str
    task: str
    no_llm: bool
    profile: dict[str, Any] | None
    plan: list[str]
    evidence: Annotated[list[dict[str, Any]], operator.add]
    report: dict[str, Any] | None
    markdown_report_path: str | None
    json_report_path: str | None
    errors: Annotated[list[str], operator.add]
    warnings: Annotated[list[str], operator.add]
    llm_used: bool
    llm_model: str | None
    analysis_mode: str


def create_initial_state(
    project_root: str,
    task: str,
    no_llm: bool = True,
    llm_model: str | None = None,
) -> RepoInsightState:
    """Create an initial workflow state."""
    return {
        "project_root": project_root,
        "task": task,
        "no_llm": no_llm,
        "profile": None,
        "plan": [],
        "evidence": [],
        "report": None,
        "markdown_report_path": None,
        "json_report_path": None,
        "errors": [],
        "warnings": [],
        "llm_used": False,
        "llm_model": llm_model,
        "analysis_mode": "deterministic" if no_llm else "llm",
    }
