from __future__ import annotations

from pathlib import Path

import pytest

from repoinsight.tools.report_tools import write_report
from repoinsight.utils import report_guard
from repoinsight.utils.report_guard import ReportWriteError


def test_write_report_writes_markdown_under_reports(tmp_path: Path) -> None:
    project = tmp_path / "project"
    project.mkdir()

    result = write_report(str(project), "analysis.md", "# Report\n")
    report_path = Path(result["report_path"])

    assert report_path == project.resolve() / "reports" / "analysis.md"
    assert report_path.read_text(encoding="utf-8") == "# Report\n"
    assert result["size_chars"] == len("# Report\n")


def test_write_report_rejects_non_markdown_filename(tmp_path: Path) -> None:
    project = tmp_path / "project"
    project.mkdir()

    with pytest.raises(ValueError, match=".md"):
        write_report(str(project), "analysis.txt", "bad")


def test_write_report_rejects_path_traversal(tmp_path: Path) -> None:
    project = tmp_path / "project"
    project.mkdir()

    with pytest.raises(ValueError, match="directories"):
        write_report(str(project), "../analysis.md", "bad")

    with pytest.raises(ValueError, match="directories"):
        write_report(str(project), "nested/analysis.md", "bad")


def test_write_report_reports_unwritable_reports_directory(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    project = tmp_path / "project"
    project.mkdir()
    reports_dir = project / "reports"
    reports_dir.mkdir()
    resolved_reports = reports_dir.resolve()

    def fake_access(path: str | Path, mode: int) -> bool:
        return Path(path).resolve(strict=False) != resolved_reports

    monkeypatch.setattr(report_guard.os, "access", fake_access)

    with pytest.raises(ReportWriteError, match="Reports directory is not writable"):
        write_report(str(project), "analysis.md", "# Report\n")


def test_write_report_reports_unwritable_existing_file(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    project = tmp_path / "project"
    project.mkdir()
    reports_dir = project / "reports"
    reports_dir.mkdir()
    report_path = reports_dir / "analysis.md"
    report_path.write_text("old", encoding="utf-8")
    resolved_report = report_path.resolve()

    def fake_access(path: str | Path, mode: int) -> bool:
        if Path(path).resolve(strict=False) == resolved_report:
            return False
        return True

    monkeypatch.setattr(report_guard.os, "access", fake_access)

    with pytest.raises(ReportWriteError, match="Report file is not writable"):
        write_report(str(project), "analysis.md", "# Report\n")
