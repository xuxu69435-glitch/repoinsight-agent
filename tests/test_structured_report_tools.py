from __future__ import annotations

import json
from pathlib import Path

import pytest

from repoinsight.agent.schemas import AnalysisReport, ProjectSummary
from repoinsight.reporting.json_writer import write_json_report
from repoinsight.tools.report_tools import write_structured_report


def _sample_report_dict() -> dict:
    return {
        "title": "Structured Demo",
        "task": "Analyze project",
        "project_summary": {
            "project_types": ["Python"],
            "languages": ["Python"],
            "frameworks": ["Typer CLI"],
            "entry_points": ["repoinsight/cli.py"],
            "key_config_files": ["pyproject.toml"],
        },
        "executive_summary": "Demo summary.",
        "findings": [
            {
                "title": "CLI exists",
                "severity": "info",
                "category": "architecture",
                "description": "A CLI entry point was detected.",
                "evidence": [
                    {
                        "file_path": "repoinsight/cli.py",
                        "summary": "CLI module path appears in project profile.",
                    }
                ],
                "confidence": 0.8,
            }
        ],
        "recommendations": [],
        "evidence_files": ["repoinsight/cli.py"],
        "limitations": ["Synthetic test data."],
        "next_steps": ["Run full analysis."],
    }


def test_write_json_report_writes_json_under_reports(tmp_path: Path) -> None:
    project = tmp_path / "project"
    project.mkdir()
    report = AnalysisReport(
        title="JSON Demo",
        task="Analyze",
        executive_summary="Summary",
        project_summary=ProjectSummary(entry_points=["repoinsight/cli.py"]),
    )

    result = write_json_report(str(project), "analysis_report.json", report)
    report_path = Path(result["report_path"])
    parsed = json.loads(report_path.read_text(encoding="utf-8"))

    assert report_path == project.resolve() / "reports" / "analysis_report.json"
    assert parsed["title"] == "JSON Demo"
    assert "repoinsight/cli.py" in parsed["project_summary"]["entry_points"]
    assert str(project.resolve()) not in report_path.read_text(encoding="utf-8")


def test_write_json_report_rejects_bad_filename(tmp_path: Path) -> None:
    project = tmp_path / "project"
    project.mkdir()
    report = AnalysisReport()

    with pytest.raises(ValueError, match="directories"):
        write_json_report(str(project), "../bad.json", report)
    with pytest.raises(ValueError, match=".json"):
        write_json_report(str(project), "bad.md", report)


def test_write_structured_report_accepts_dict_and_writes_md_and_json(tmp_path: Path) -> None:
    project = tmp_path / "project"
    project.mkdir()

    result = write_structured_report(str(project), "analysis_report.json", _sample_report_dict())

    markdown_path = Path(result["markdown_report_path"])
    json_path = Path(result["json_report_path"])
    assert markdown_path == project.resolve() / "reports" / "analysis_report.md"
    assert json_path == project.resolve() / "reports" / "analysis_report.json"
    assert markdown_path.read_text(encoding="utf-8").startswith("# Structured Demo")
    assert json.loads(json_path.read_text(encoding="utf-8"))["title"] == "Structured Demo"
    assert result["markdown_size_chars"] > 0
    assert result["json_size_chars"] > 0


def test_write_structured_report_accepts_markdown_filename(tmp_path: Path) -> None:
    project = tmp_path / "project"
    project.mkdir()

    result = write_structured_report(str(project), "analysis_report.md", _sample_report_dict())

    assert result["markdown_report_path"].endswith("analysis_report.md")
    assert result["json_report_path"].endswith("analysis_report.json")


def test_write_structured_report_rejects_dangerous_filename(tmp_path: Path) -> None:
    project = tmp_path / "project"
    project.mkdir()

    with pytest.raises(ValueError, match="directories"):
        write_structured_report(str(project), "../analysis_report.json", _sample_report_dict())
    with pytest.raises(ValueError, match="may only contain"):
        write_structured_report(str(project), "analysis report.json", _sample_report_dict())
