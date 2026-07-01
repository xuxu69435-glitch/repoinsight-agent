"""Guards for writing generated reports inside a project."""

from __future__ import annotations

import os
from pathlib import Path

from repoinsight.utils.path_guard import ensure_path_in_project

REPORTS_DIR_NOT_WRITABLE = (
    "Reports directory is not writable: {path}. Please check permissions or "
    "remove/recreate the generated reports directory."
)
REPORT_FILE_NOT_WRITABLE = (
    "Report file is not writable: {path}. Please check file permissions or "
    "choose another report filename."
)


class ReportWriteError(RuntimeError):
    """Raised when RepoInsight cannot write a generated report."""


def ensure_reports_dir(project_root: Path) -> Path:
    """Ensure project_root/reports exists, is a directory, and is writable."""
    root = project_root.expanduser().resolve(strict=True)
    reports_dir = ensure_path_in_project(root, root / "reports")

    if reports_dir.exists() and not reports_dir.is_dir():
        raise ReportWriteError(
            f"Reports path is not a directory: {reports_dir}. "
            "Please remove/recreate the generated reports path."
        )

    try:
        reports_dir.mkdir(parents=True, exist_ok=True)
    except PermissionError as exc:
        raise ReportWriteError(_reports_dir_not_writable_message(reports_dir)) from exc
    except OSError as exc:
        raise ReportWriteError(
            f"Reports directory cannot be created: {reports_dir}. {exc}"
        ) from exc

    if not os.access(reports_dir, os.W_OK):
        raise ReportWriteError(_reports_dir_not_writable_message(reports_dir))

    return reports_dir


def check_file_writable(path: Path) -> bool:
    """Return whether an existing report file or its parent directory is writable."""
    target = path.expanduser().resolve(strict=False)
    if target.exists():
        if not target.is_file() or not os.access(target, os.W_OK):
            return False
        try:
            with target.open("r+b"):
                return True
        except OSError:
            return False
    parent = target.parent
    return parent.exists() and parent.is_dir() and os.access(parent, os.W_OK)


def ensure_report_file_writable(path: Path) -> Path:
    """Raise a clear error if a report file path cannot be written."""
    target = path.expanduser().resolve(strict=False)
    if check_file_writable(target):
        return target
    if target.exists():
        raise ReportWriteError(_report_file_not_writable_message(target))
    raise ReportWriteError(_reports_dir_not_writable_message(target.parent))


def report_write_error_for_exception(path: Path, exc: OSError) -> ReportWriteError:
    """Translate write exceptions into stable user-facing report errors."""
    target = path.expanduser().resolve(strict=False)
    if isinstance(exc, PermissionError):
        if target.exists():
            return ReportWriteError(_report_file_not_writable_message(target))
        return ReportWriteError(_reports_dir_not_writable_message(target.parent))
    return ReportWriteError(f"Could not write report file: {target}. {exc}")


def _reports_dir_not_writable_message(path: Path) -> str:
    return REPORTS_DIR_NOT_WRITABLE.format(path=path)


def _report_file_not_writable_message(path: Path) -> str:
    return REPORT_FILE_NOT_WRITABLE.format(path=path)
