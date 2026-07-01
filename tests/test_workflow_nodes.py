from __future__ import annotations

import json
from pathlib import Path

from repoinsight.agent.schemas import AnalysisReport
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


def test_plan_node_with_llm_falls_back_to_deterministic_warning() -> None:
    state = create_initial_state("project", "Analyze", no_llm=False)

    result = plan_node(state)

    assert result["plan"]
    assert "LLM workflow analysis is not implemented yet" in result["warnings"][0]


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


def test_analyze_node_generates_analysis_report() -> None:
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

    assert report.findings
    assert report.limitations
    assert report.project_summary.project_types == ["Python"]


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
