"""Prompt snippets for workflow analysis."""

from __future__ import annotations

WORKFLOW_ANALYSIS_PROMPT = """\
Analyze the repository evidence and return an AnalysisReport.

Workflow analysis defaults to deterministic no-LLM mode. When LLM mode is used,
the model must only use the already-collected profile, plan, and evidence.
"""
