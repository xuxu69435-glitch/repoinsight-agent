"""Markdown rendering for structured analysis reports."""

from __future__ import annotations

from repoinsight.agent.schemas import AnalysisReport, EvidenceItem


def render_analysis_report(report: AnalysisReport) -> str:
    """Render an AnalysisReport as human-readable Markdown."""
    lines: list[str] = [
        f"# {report.title}",
        "",
        "## Task",
        "",
        report.task or "None reported.",
        "",
        "## Executive Summary",
        "",
        report.executive_summary or "None reported.",
        "",
        "## Project Summary",
        "",
        f"- Project Types: {_join_or_none(report.project_summary.project_types)}",
        f"- Languages: {_join_or_none(report.project_summary.languages)}",
        f"- Frameworks: {_join_or_none(report.project_summary.frameworks)}",
        f"- Package Managers: {_join_or_none(report.project_summary.package_managers)}",
        f"- Entry Points: {_join_or_none(report.project_summary.entry_points)}",
        f"- Key Config Files: {_join_or_none(report.project_summary.key_config_files)}",
        "",
        "## Findings",
        "",
    ]
    lines.extend(_render_findings(report))
    lines.extend(["", "## Recommendations", ""])
    lines.extend(_render_recommendations(report))
    lines.extend(["", "## Evidence Files", ""])
    lines.extend(_render_simple_list(report.evidence_files))
    lines.extend(["", "## Limitations", ""])
    lines.extend(_render_simple_list(report.limitations))
    lines.extend(["", "## Next Steps", ""])
    lines.extend(_render_simple_list(report.next_steps))
    lines.append("")
    return "\n".join(lines)


def _render_findings(report: AnalysisReport) -> list[str]:
    if not report.findings:
        return ["None reported."]

    lines: list[str] = []
    for index, finding in enumerate(report.findings, start=1):
        lines.extend(
            [
                f"### {index}. {finding.title}",
                "",
                f"- Severity: {finding.severity}",
                f"- Category: {finding.category}",
                f"- Confidence: {finding.confidence:.2f}",
                "",
                finding.description or "None reported.",
                "",
                "Evidence:",
            ]
        )
        lines.extend(_render_evidence(finding.evidence))
        lines.append("")
    return lines


def _render_recommendations(report: AnalysisReport) -> list[str]:
    if not report.recommendations:
        return ["None reported."]

    lines: list[str] = []
    for index, recommendation in enumerate(report.recommendations, start=1):
        lines.extend(
            [
                f"### {index}. {recommendation.title}",
                "",
                f"- Priority: {recommendation.priority}",
                "",
                recommendation.description or "None reported.",
                "",
                "Suggested Steps:",
            ]
        )
        lines.extend(_render_simple_list(recommendation.suggested_steps))
        lines.extend(["", "Related Findings:"])
        lines.extend(_render_simple_list(recommendation.related_findings))
        lines.append("")
    return lines


def _render_evidence(items: list[EvidenceItem]) -> list[str]:
    if not items:
        return ["- None reported."]

    lines: list[str] = []
    for item in items:
        prefix = "Evidence"
        location = ""
        if item.command:
            prefix = "Command Evidence"
            location = f" `{item.command}`"
        elif item.file_path:
            prefix = "File Evidence"
            location = f" `{item.file_path}`"
            if item.line is not None:
                location += f":{item.line}"
        lines.append(f"- {prefix}{location}: {item.summary or 'None reported.'}")
        if item.raw_excerpt:
            lines.extend(["", "  ```text", f"  {item.raw_excerpt}", "  ```"])
    return lines


def _render_simple_list(items: list[str]) -> list[str]:
    if not items:
        return ["None reported."]
    return [f"- {item}" for item in items]


def _join_or_none(items: list[str]) -> str:
    if not items:
        return "None reported."
    return ", ".join(items)
