from __future__ import annotations

import pytest
from pydantic import ValidationError

from repoinsight.agent.schemas import (
    AnalysisReport,
    EvidenceItem,
    Finding,
    ProjectSummary,
    Recommendation,
)
from repoinsight.reporting.markdown_renderer import render_analysis_report


def test_analysis_report_can_be_created_with_minimal_fields() -> None:
    report = AnalysisReport(task="Analyze project", executive_summary="Looks healthy.")

    assert report.title == "RepoInsight Analysis Report"
    assert report.generated_by == "RepoInsight Agent"
    assert report.project_summary.project_types == []


def test_finding_rejects_invalid_severity() -> None:
    with pytest.raises(ValidationError):
        Finding(title="Bad", severity="urgent")


def test_recommendation_rejects_invalid_priority() -> None:
    with pytest.raises(ValidationError):
        Recommendation(title="Bad", priority="urgent")


def test_finding_confidence_must_be_between_zero_and_one() -> None:
    with pytest.raises(ValidationError):
        Finding(title="Bad", confidence=1.5)


def test_report_rejects_absolute_paths() -> None:
    with pytest.raises(ValidationError):
        AnalysisReport(evidence_files=["C:/secret/file.py"])


def test_render_analysis_report_outputs_sections_and_evidence() -> None:
    report = AnalysisReport(
        title="Demo Report",
        task="Review project",
        executive_summary="The project is small.",
        project_summary=ProjectSummary(
            project_types=["Python"],
            languages=["Python"],
            entry_points=["repoinsight/cli.py"],
            key_config_files=["pyproject.toml"],
        ),
        findings=[
            Finding(
                title="CLI entry point exists",
                category="architecture",
                description="The CLI module is present.",
                confidence=0.9,
                evidence=[
                    EvidenceItem(
                        file_path="repoinsight/cli.py",
                        line=1,
                        summary="CLI source file exists.",
                    ),
                    EvidenceItem(
                        command="python -m pytest",
                        summary="Tests passed.",
                        raw_excerpt="50 passed",
                    ),
                ],
            )
        ],
        recommendations=[
            Recommendation(
                title="Keep CLI covered",
                description="Maintain tests around CLI behavior.",
                suggested_steps=["Add tests for new commands."],
            )
        ],
        evidence_files=["repoinsight/cli.py"],
        limitations=["No LLM call in test."],
        next_steps=["Run integration test with API key."],
    )

    rendered = render_analysis_report(report)

    assert "# Demo Report" in rendered
    assert "## Findings" in rendered
    assert "File Evidence `repoinsight/cli.py`:1" in rendered
    assert "Command Evidence `python -m pytest`" in rendered
    assert "## Recommendations" in rendered


def test_render_analysis_report_handles_empty_lists() -> None:
    rendered = render_analysis_report(AnalysisReport())

    assert "None reported." in rendered
