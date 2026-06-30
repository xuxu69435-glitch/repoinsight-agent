"""Markdown report writing tools."""

from __future__ import annotations

from pathlib import Path, PurePosixPath, PureWindowsPath
from typing import Any

from repoinsight.utils.path_guard import ensure_path_in_project, resolve_project_path


def write_report(project_root: str, filename: str, content: str) -> dict[str, Any]:
    """Write a Markdown report into project_root/reports."""
    safe_name = _validate_report_filename(filename)
    root = resolve_project_path(project_root)
    reports_dir = ensure_path_in_project(root, root / "reports")
    reports_dir.mkdir(parents=True, exist_ok=True)

    report_path = ensure_path_in_project(root, reports_dir / safe_name)
    report_path.write_text(content, encoding="utf-8")

    return {"report_path": str(report_path), "size_chars": len(content)}


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
