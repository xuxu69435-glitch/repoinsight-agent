from __future__ import annotations

import json
from pathlib import Path

from repoinsight.workflow.graph import build_workflow, run_workflow


def test_build_workflow_compiles() -> None:
    graph = build_workflow()

    assert graph is not None


def test_run_workflow_completes_without_api_key(monkeypatch, tmp_path: Path) -> None:
    project = tmp_path / "project"
    project.mkdir()
    (project / "README.md").write_text("# Demo\n", encoding="utf-8")
    (project / "pyproject.toml").write_text(
        "[project]\nname = 'demo'\ndependencies = ['typer>=0.12']\n",
        encoding="utf-8",
    )
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    result = run_workflow(str(project), "Analyze open source readiness", no_llm=True)

    assert result["errors"] == []
    assert result["profile"]["project_types"] == ["Python"]
    assert result["markdown_report_path"].endswith("workflow_analysis_report.md")
    assert result["json_report_path"].endswith("workflow_analysis_report.json")
    assert Path(result["markdown_report_path"]).is_file()
    json_path = Path(result["json_report_path"])
    assert json_path.is_file()
    assert json.loads(json_path.read_text(encoding="utf-8"))["task"] == (
        "Analyze open source readiness"
    )
