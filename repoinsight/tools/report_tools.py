"""Markdown report writing tools."""

from __future__ import annotations

import re
from pathlib import Path, PurePosixPath, PureWindowsPath
from typing import Any

from repoinsight.agent.schemas import AnalysisReport
from repoinsight.reporting.json_writer import write_json_report
from repoinsight.reporting.markdown_renderer import render_analysis_report
from repoinsight.utils.path_guard import ensure_path_in_project, resolve_project_path
from repoinsight.utils.report_guard import (
    ensure_report_file_writable,
    ensure_reports_dir,
    report_write_error_for_exception,
)


def write_report(project_root: str, filename: str, content: str) -> dict[str, Any]:
    """Write a Markdown report into project_root/reports."""
    safe_name = _validate_report_filename(filename)
    root = resolve_project_path(project_root)
    reports_dir = ensure_reports_dir(root)

    report_path = ensure_path_in_project(root, reports_dir / safe_name)
    ensure_report_file_writable(report_path)
    try:
        report_path.write_text(content, encoding="utf-8")
    except OSError as exc:
        raise report_write_error_for_exception(report_path, exc) from exc

    return {"report_path": str(report_path), "size_chars": len(content)}


def write_structured_report(
    project_root: str,
    filename: str,
    report: AnalysisReport | dict[str, Any],
) -> dict[str, Any]:
    """Write a structured report as both Markdown and JSON under reports/."""
    base_name = _validate_structured_report_filename(filename)
    analysis_report = (
        report if isinstance(report, AnalysisReport) else AnalysisReport.model_validate(report)
    )

    markdown_content = render_analysis_report(analysis_report)
    markdown_result = write_report(project_root, f"{base_name}.md", markdown_content)
    json_result = write_json_report(project_root, f"{base_name}.json", analysis_report)

    return {
        "markdown_report_path": markdown_result["report_path"],
        "json_report_path": json_result["report_path"],
        "markdown_size_chars": markdown_result["size_chars"],
        "json_size_chars": json_result["size_chars"],
    }


def _validate_report_filename(filename: str) -> str:
    if not filename or not filename.strip():
        raise ValueError("Report filename must not be empty.")
    if "/" in filename or "\\" in filename:
        raise ValueError("Report filename must not contain directories.")

    windows_path = PureWindowsPath(filename)
    posix_path = PurePosixPath(filename)
    if windows_path.is_absolute() or posix_path.is_absolute():
        raise ValueError("Report filename must be a simple .md filename.")
    if len(windows_path.parts) != 1 or len(posix_path.parts) != 1:
        raise ValueError("Report filename must be a simple .md filename.")
    if filename in {".", ".."}:
        raise ValueError("Report filename must be a simple .md filename.")
    if Path(filename).suffix.lower() != ".md":
        raise ValueError("Report filename must use the .md extension.")

    return filename


def _validate_structured_report_filename(filename: str) -> str:
    if not filename or not filename.strip():
        raise ValueError("Report filename must not be empty.")
    if "/" in filename or "\\" in filename:
        raise ValueError("Report filename must not contain directories.")

    windows_path = PureWindowsPath(filename)
    posix_path = PurePosixPath(filename)
    if windows_path.is_absolute() or posix_path.is_absolute():
        raise ValueError("Report filename must be a simple .md or .json filename.")
    if len(windows_path.parts) != 1 or len(posix_path.parts) != 1:
        raise ValueError("Report filename must be a simple .md or .json filename.")

    path = Path(filename)
    if path.suffix.lower() not in {".md", ".json"}:
        raise ValueError("Report filename must use the .md or .json extension.")

    base_name = path.stem
    if not re.fullmatch(r"[A-Za-z0-9_-]+", base_name):
        raise ValueError(
            "Report filename may only contain English letters, digits, underscores, "
            "hyphens, and one extension dot."
        )

    return base_name
