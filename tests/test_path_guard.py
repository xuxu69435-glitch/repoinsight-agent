from __future__ import annotations

from pathlib import Path

import pytest

from repoinsight.utils.path_guard import ensure_path_in_project, resolve_project_path


def test_resolve_project_path_requires_existing_directory(tmp_path: Path) -> None:
    project = tmp_path / "project"
    project.mkdir()

    assert resolve_project_path(str(project)) == project.resolve()

    with pytest.raises(FileNotFoundError, match="Project path does not exist"):
        resolve_project_path(str(tmp_path / "missing"))

    file_path = tmp_path / "file.txt"
    file_path.write_text("hello", encoding="utf-8")
    with pytest.raises(NotADirectoryError, match="Project path is not a directory"):
        resolve_project_path(str(file_path))


def test_ensure_path_in_project_blocks_escape(tmp_path: Path) -> None:
    project = tmp_path / "project"
    project.mkdir()
    inside = project / "README.md"
    inside.write_text("inside", encoding="utf-8")

    outside = tmp_path / "outside.md"
    outside.write_text("outside", encoding="utf-8")

    assert ensure_path_in_project(project, Path("README.md")) == inside.resolve()
    with pytest.raises(PermissionError, match="outside project root"):
        ensure_path_in_project(project, outside)


def test_ensure_path_in_project_blocks_parent_traversal(tmp_path: Path) -> None:
    project = tmp_path / "project"
    project.mkdir()

    with pytest.raises(PermissionError, match="outside project root"):
        ensure_path_in_project(project, Path("..") / "secret.txt")
