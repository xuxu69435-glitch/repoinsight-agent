"""JSON report writer."""

from __future__ import annotations

import json
from pathlib import Path, PurePosixPath, PureWindowsPath
from typing import Any

from repoinsight.agent.schemas import AnalysisReport
from repoinsight.utils.path_guard import ensure_path_in_project, resolve_project_path
from repoinsight.utils.report_guard import (
    ensure_report_file_writable,
    ensure_reports_dir,
    report_write_error_for_exception,
)


def write_json_report(project_root: str, filename: str, report: AnalysisReport) -> dict[str, Any]:
    """Write an AnalysisReport JSON file under project_root/reports."""
    safe_name = _validate_json_filename(filename)
    root = resolve_project_path(project_root)
    reports_dir = ensure_reports_dir(root)

    report_path = ensure_path_in_project(root, reports_dir / safe_name)
    content = json.dumps(report.model_dump(), ensure_ascii=False, indent=2)
    ensure_report_file_writable(report_path)
    try:
        report_path.write_text(content, encoding="utf-8")
    except OSError as exc:
        raise report_write_error_for_exception(report_path, exc) from exc

    return {"report_path": str(report_path), "size_chars": len(content)}


def _validate_json_filename(filename: str) -> str:
    if not filename or not filename.strip():
        raise ValueError("Report filename must not be empty.")
    if "/" in filename or "\\" in filename:
        raise ValueError("Report filename must not contain directories.")

    windows_path = PureWindowsPath(filename)
    posix_path = PurePosixPath(filename)
    if windows_path.is_absolute() or posix_path.is_absolute():
        raise ValueError("Report filename must be a simple .json filename.")
    if len(windows_path.parts) != 1 or len(posix_path.parts) != 1:
        raise ValueError("Report filename must be a simple .json filename.")
    if filename in {".", ".."}:
        raise ValueError("Report filename must be a simple .json filename.")
    if Path(filename).suffix.lower() != ".json":
        raise ValueError("Report filename must use the .json extension.")

    return filename
