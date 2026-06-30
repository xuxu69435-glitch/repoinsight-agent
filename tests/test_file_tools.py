from __future__ import annotations

from pathlib import Path

import pytest

from repoinsight.tools.file_tools import list_files, read_file


def test_list_files_ignores_dependency_and_git_directories(tmp_path: Path) -> None:
    project = tmp_path / "project"
    (project / "src").mkdir(parents=True)
    (project / "src" / "app.py").write_text("print('hello')", encoding="utf-8")
    (project / "node_modules" / "pkg").mkdir(parents=True)
    (project / "node_modules" / "pkg" / "index.js").write_text("ignored", encoding="utf-8")
    (project / ".git").mkdir()
    (project / ".git" / "config").write_text("ignored", encoding="utf-8")

    result = list_files(str(project), max_depth=3)

    assert "src" in result["directories"]
    assert "src/app.py" in result["files"]
    assert all("node_modules" not in path for path in result["directories"])
    assert all("node_modules" not in path for path in result["files"])
    assert all(".git" not in path for path in result["directories"])
    assert all(".git" not in path for path in result["files"])


def test_read_file_reads_text_file(tmp_path: Path) -> None:
    project = tmp_path / "project"
    project.mkdir()
    (project / "README.md").write_text("hello repo", encoding="utf-8")

    result = read_file(str(project), "README.md")

    assert result["path"] == "README.md"
    assert result["content"] == "hello repo"
    assert result["truncated"] is False
    assert result["size_chars"] == len("hello repo")


def test_read_file_truncates_long_text(tmp_path: Path) -> None:
    project = tmp_path / "project"
    project.mkdir()
    (project / "long.txt").write_text("abcdef", encoding="utf-8")

    result = read_file(str(project), "long.txt", max_chars=3)

    assert result["content"] == "abc"
    assert result["truncated"] is True
    assert result["size_chars"] == 3


def test_read_file_rejects_binary_file(tmp_path: Path) -> None:
    project = tmp_path / "project"
    project.mkdir()
    (project / "data.bin").write_bytes(b"abc\x00def")

    with pytest.raises(ValueError, match="Refusing to read binary file"):
        read_file(str(project), "data.bin")
