from __future__ import annotations

import os
from pathlib import Path

import pytest

from repoinsight.utils import report_guard
from repoinsight.utils.report_guard import (
    ReportWriteError,
    check_file_writable,
    ensure_reports_dir,
)


def test_ensure_reports_dir_creates_missing_directory(tmp_path: Path) -> None:
    project = tmp_path / "project"
    project.mkdir()

    reports_dir = ensure_reports_dir(project)

    assert reports_dir == project.resolve() / "reports"
    assert reports_dir.is_dir()


def test_ensure_reports_dir_rejects_reports_file(tmp_path: Path) -> None:
    project = tmp_path / "project"
    project.mkdir()
    (project / "reports").write_text("not a directory", encoding="utf-8")

    with pytest.raises(ReportWriteError, match="Reports path is not a directory"):
        ensure_reports_dir(project)


def test_ensure_reports_dir_reports_unwritable_directory(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    project = tmp_path / "project"
    project.mkdir()
    reports_dir = project / "reports"
    reports_dir.mkdir()
    resolved_reports = reports_dir.resolve()

    def fake_access(path: str | Path, mode: int) -> bool:
        if Path(path).resolve(strict=False) == resolved_reports and mode == os.W_OK:
            return False
        return True

    monkeypatch.setattr(report_guard.os, "access", fake_access)

    with pytest.raises(ReportWriteError, match="Reports directory is not writable"):
        ensure_reports_dir(project)


def test_check_file_writable_checks_existing_file(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    report_path = tmp_path / "report.md"
    report_path.write_text("# Report\n", encoding="utf-8")
    resolved_report = report_path.resolve()

    def fake_access(path: str | Path, mode: int) -> bool:
        if Path(path).resolve(strict=False) == resolved_report and mode == os.W_OK:
            return False
        return True

    monkeypatch.setattr(report_guard.os, "access", fake_access)

    assert check_file_writable(report_path) is False


def test_check_file_writable_checks_parent_for_missing_file(tmp_path: Path) -> None:
    reports_dir = tmp_path / "reports"
    reports_dir.mkdir()

    assert check_file_writable(reports_dir / "new.md") is True
