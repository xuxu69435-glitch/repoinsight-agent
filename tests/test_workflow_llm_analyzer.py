from __future__ import annotations

import json
from typing import Any

import pytest

from repoinsight.config import AppConfig
from repoinsight.workflow.llm_analyzer import (
    analyze_with_llm,
    build_llm_analysis_prompt,
    extract_json_object,
)


def test_extract_json_object_parses_valid_json() -> None:
    assert extract_json_object('  {"title": "Report"}  ') == {"title": "Report"}


def test_extract_json_object_rejects_non_json() -> None:
    with pytest.raises(ValueError, match="not valid JSON"):
        extract_json_object("not json")


def test_build_llm_analysis_prompt_contains_constraints() -> None:
    prompt = build_llm_analysis_prompt(
        task="Analyze open-source readiness",
        profile={"evidence_files": ["pyproject.toml"]},
        plan=["Inspect project profile"],
        evidence=[{"kind": "key_file", "file_path": "pyproject.toml"}],
    )

    assert "Analyze open-source readiness" in prompt
    assert "Do not invent files, commands, dependencies, or results." in prompt
    assert "Return a valid JSON object matching the AnalysisReport schema." in prompt
    assert "Do not include Markdown fences." in prompt


def test_analyze_with_llm_validates_mock_json(monkeypatch) -> None:
    payload = _report_payload()

    class FakeLLM:
        def invoke(self, prompt: str) -> str:
            assert "Analyze project" in prompt
            return json.dumps(payload)

    monkeypatch.setattr(
        "repoinsight.workflow.llm_analyzer.build_workflow_llm",
        lambda config: FakeLLM(),
    )

    report = analyze_with_llm(
        task="Analyze project",
        profile=_profile(),
        plan=["Inspect project profile"],
        evidence=_evidence(),
        config=AppConfig(openai_api_key="test-key"),
    )

    assert report.title == "Mock LLM Report"
    assert report.evidence_files == ["pyproject.toml"]


def test_analyze_with_llm_rejects_invalid_json(monkeypatch) -> None:
    class FakeLLM:
        def invoke(self, prompt: str) -> str:
            return "not json"

    monkeypatch.setattr(
        "repoinsight.workflow.llm_analyzer.build_workflow_llm",
        lambda config: FakeLLM(),
    )

    with pytest.raises(ValueError, match="not valid JSON"):
        analyze_with_llm(
            task="Analyze project",
            profile=_profile(),
            plan=[],
            evidence=_evidence(),
            config=AppConfig(openai_api_key="test-key"),
        )


def test_analyze_with_llm_rejects_schema_invalid_json(monkeypatch) -> None:
    class FakeLLM:
        def invoke(self, prompt: str) -> str:
            return json.dumps({"findings": [{"title": "Bad confidence", "confidence": 2}]})

    monkeypatch.setattr(
        "repoinsight.workflow.llm_analyzer.build_workflow_llm",
        lambda config: FakeLLM(),
    )

    with pytest.raises(ValueError, match="did not match AnalysisReport schema"):
        analyze_with_llm(
            task="Analyze project",
            profile=_profile(),
            plan=[],
            evidence=_evidence(),
            config=AppConfig(openai_api_key="test-key"),
        )


def test_analyze_with_llm_rejects_invented_evidence_files(monkeypatch) -> None:
    payload = _report_payload(evidence_files=["invented.py"])

    class FakeLLM:
        def invoke(self, prompt: str) -> str:
            return json.dumps(payload)

    monkeypatch.setattr(
        "repoinsight.workflow.llm_analyzer.build_workflow_llm",
        lambda config: FakeLLM(),
    )

    with pytest.raises(ValueError, match="not present in workflow evidence"):
        analyze_with_llm(
            task="Analyze project",
            profile=_profile(),
            plan=[],
            evidence=_evidence(),
            config=AppConfig(openai_api_key="test-key"),
        )


def _report_payload(**overrides: Any) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "title": "Mock LLM Report",
        "task": "Analyze project",
        "project_summary": {
            "project_types": ["Python"],
            "languages": ["Python"],
            "frameworks": ["Typer CLI"],
            "package_managers": [],
            "entry_points": ["repoinsight/cli.py"],
            "key_config_files": ["pyproject.toml"],
        },
        "executive_summary": "Mock LLM analysis based on workflow evidence.",
        "findings": [
            {
                "title": "Detected Python CLI",
                "category": "project-profile",
                "description": "The profile identifies a Python CLI project.",
                "evidence": [
                    {
                        "file_path": "pyproject.toml",
                        "summary": "Project metadata evidence.",
                    }
                ],
                "confidence": 0.9,
            }
        ],
        "recommendations": [
            {
                "title": "Review release readiness",
                "priority": "medium",
                "description": "Confirm packaging metadata before release.",
                "suggested_steps": ["Review pyproject.toml."],
                "related_findings": ["Detected Python CLI"],
            }
        ],
        "evidence_files": ["pyproject.toml"],
        "limitations": ["Only provided workflow evidence was used."],
        "next_steps": ["Review generated report."],
    }
    payload.update(overrides)
    return payload


def _profile() -> dict[str, Any]:
    return {
        "project_types": ["Python"],
        "languages": ["Python"],
        "frameworks": ["Typer CLI"],
        "entry_points": [{"path": "repoinsight/cli.py"}],
        "config_files": [{"path": "pyproject.toml"}],
        "evidence_files": ["pyproject.toml", "repoinsight/cli.py"],
        "confidence": 0.8,
    }


def _evidence() -> list[dict[str, Any]]:
    return [
        {"kind": "key_file", "file_path": "pyproject.toml"},
        {"kind": "project_profile", "data": _profile()},
    ]
