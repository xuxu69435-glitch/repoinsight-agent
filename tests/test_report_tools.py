from __future__ import annotations

from pathlib import Path

import pytest

from repoinsight.tools.report_tools import write_report


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
