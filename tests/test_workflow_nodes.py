from __future__ import annotations

import json
from pathlib import Path

from repoinsight.agent.schemas import AnalysisReport
from repoinsight.config import AppConfig
from repoinsight.workflow.nodes import (
    analyze_node,
    evidence_node,
    plan_node,
    profile_node,
    report_node,
)
from repoinsight.workflow.state import create_initial_state


def test_profile_node_writes_profile_for_unknown_project(tmp_path: Path) -> None:
    project = tmp_path / "project"
    project.mkdir()
    (project / "random.txt").write_text("hello\n", encoding="utf-8")
    state = create_initial_state(str(project), "Analyze")

    result = profile_node(state)

    assert result["profile"]["project_types"] == ["unknown"]
    assert "errors" not in result


def test_plan_node_generates_non_empty_plan() -> None:
    state = create_initial_state("project", "Analyze", no_llm=True)

    result = plan_node(state)

    assert result["plan"]
    assert "Inspect project profile" in result["plan"]


def test_plan_node_with_llm_only_generates_plan() -> None:
    state = create_initial_state("project", "Analyze", no_llm=False)

    result = plan_node(state)

    assert result["plan"]
    assert "warnings" not in result


def test_evidence_node_collects_evidence_without_git_repo(tmp_path: Path) -> None:
    project = tmp_path / "project"
    project.mkdir()
    (project / "README.md").write_text("# Demo\n", encoding="utf-8")
    (project / "pyproject.toml").write_text("[project]\nname = 'demo'\n", encoding="utf-8")
    state = create_initial_state(str(project), "Analyze")
    state.update(profile=profile_node(state)["profile"])

    result = evidence_node(state)

    kinds = {item["kind"] for item in result["evidence"]}
    assert "project_profile" in kinds
    assert "git_status" in kinds
    assert "git_diff_stat" in kinds
    assert "key_file" in kinds


def test_analyze_node_generates_analysis_report_without_llm(monkeypatch) -> None:
    def fail_analyze_with_llm(*args, **kwargs):
        raise AssertionError("analyze_with_llm should not be called")

    monkeypatch.setattr("repoinsight.workflow.nodes.analyze_with_llm", fail_analyze_with_llm)
    state = create_initial_state("project", "Analyze", no_llm=True)
    state["profile"] = {
        "project_types": ["Python"],
        "languages": ["Python"],
        "frameworks": ["Typer CLI"],
        "entry_points": [{"path": "repoinsight/cli.py"}],
        "config_files": [{"path": "pyproject.toml"}],
        "evidence_files": ["pyproject.toml", "repoinsight/cli.py"],
        "confidence": 0.8,
        "scripts": [],
    }
    state["evidence"] = [
        {
            "kind": "git_status",
            "summary": "git status finished with exit code 0.",
            "data": {"command": "git status", "allowed": True, "exit_code": 0, "stdout": "clean"},
        }
    ]

    result = analyze_node(state)
    report = AnalysisReport.model_validate(result["report"])

    assert result["analysis_mode"] == "deterministic"
    assert result["llm_used"] is False
    assert report.findings
    assert "Deterministic workflow does not perform deep semantic code analysis." in (
        report.limitations
    )
    assert "LLM was not used." in report.limitations
    assert report.project_summary.project_types == ["Python"]


def test_analyze_node_with_llm_success(monkeypatch) -> None:
    report = AnalysisReport(
        title="LLM Report",
        task="Analyze",
        executive_summary="LLM summary",
        evidence_files=["pyproject.toml"],
    )

    def fake_analyze_with_llm(**kwargs):
        assert kwargs["config"].openai_model == "mock-model"
        return report

    monkeypatch.setattr("repoinsight.workflow.nodes.analyze_with_llm", fake_analyze_with_llm)
    state = _sample_analysis_state(no_llm=False)

    result = analyze_node(
        state,
        config=AppConfig(openai_api_key="test-key", openai_model="mock-model"),
    )

    assert result["analysis_mode"] == "llm"
    assert result["llm_used"] is True
    assert result["llm_model"] == "mock-model"
    assert AnalysisReport.model_validate(result["report"]).title == "LLM Report"


def test_analyze_node_with_llm_failure_falls_back(monkeypatch) -> None:
    def fake_analyze_with_llm(**kwargs):
        raise ValueError("invalid mock response")

    monkeypatch.setattr("repoinsight.workflow.nodes.analyze_with_llm", fake_analyze_with_llm)
    state = _sample_analysis_state(no_llm=False)

    result = analyze_node(
        state,
        config=AppConfig(openai_api_key="test-key", openai_model="mock-model"),
    )
    report = AnalysisReport.model_validate(result["report"])

    assert result["analysis_mode"] == "llm_fallback"
    assert result["llm_used"] is False
    assert result["llm_model"] == "mock-model"
    assert "invalid mock response" in result["warnings"][0]
    assert "LLM workflow analysis failed; deterministic analysis was used as fallback." in (
        report.limitations
    )


def test_report_node_writes_markdown_and_json(tmp_path: Path) -> None:
    project = tmp_path / "project"
    project.mkdir()
    state = create_initial_state(str(project), "Analyze")
    state["report"] = AnalysisReport(
        title="Workflow Report",
        task="Analyze",
        executive_summary="Summary",
    ).model_dump()

    result = report_node(state)

    markdown_path = Path(result["markdown_report_path"])
    json_path = Path(result["json_report_path"])
    assert markdown_path.name == "workflow_analysis_report.md"
    assert json_path.name == "workflow_analysis_report.json"
    assert markdown_path.is_file()
    assert json.loads(json_path.read_text(encoding="utf-8"))["title"] == "Workflow Report"


def _sample_analysis_state(no_llm: bool):
    state = create_initial_state(
        "project",
        "Analyze",
        no_llm=no_llm,
        llm_model="mock-model" if not no_llm else None,
    )
    state["profile"] = {
        "project_types": ["Python"],
        "languages": ["Python"],
        "frameworks": ["Typer CLI"],
        "entry_points": [{"path": "repoinsight/cli.py"}],
        "config_files": [{"path": "pyproject.toml"}],
        "evidence_files": ["pyproject.toml", "repoinsight/cli.py"],
        "confidence": 0.8,
        "scripts": [],
    }
    state["plan"] = ["Inspect project profile"]
    state["evidence"] = [
        {
            "kind": "git_status",
            "summary": "git status finished with exit code 0.",
            "data": {"command": "git status", "allowed": True, "exit_code": 0, "stdout": "clean"},
        }
    ]
    return state
