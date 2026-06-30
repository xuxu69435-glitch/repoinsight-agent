"""Safe file listing and reading tools."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from repoinsight.config import IGNORED_DIRECTORIES
from repoinsight.utils.path_guard import ensure_path_in_project, resolve_project_path

BINARY_CHECK_BYTES = 4096


def list_files(project_root: str, max_depth: int = 3) -> dict[str, Any]:
    """Return a shallow project directory structure without reading file content."""
    if max_depth < 0:
        raise ValueError("max_depth must be greater than or equal to 0.")

    root = resolve_project_path(project_root)
    files: list[str] = []
    directories: list[str] = []

    def walk(current: Path, depth: int) -> None:
        if depth >= max_depth:
            return

        try:
            entries = sorted(
                current.iterdir(),
                key=lambda item: (item.is_file(), item.name.lower()),
            )
        except PermissionError:
            return

        for entry in entries:
            if entry.is_dir():
                if entry.name in IGNORED_DIRECTORIES or entry.is_symlink():
                    continue
                directories.append(_relative_path(entry, root))
                walk(entry, depth + 1)
            elif entry.is_file():
                files.append(_relative_path(entry, root))

    walk(root, 0)

    return {
        "root": str(root),
        "files": sorted(files),
        "directories": sorted(directories),
        "total_files": len(files),
        "total_directories": len(directories),
    }


def read_file(project_root: str, relative_path: str, max_chars: int = 12_000) -> dict[str, Any]:
    """Read a UTF-8 text file inside project_root, truncating long content."""
    if not relative_path or not relative_path.strip():
        raise ValueError("relative_path must not be empty.")
    if max_chars <= 0:
        raise ValueError("max_chars must be greater than 0.")

    root = resolve_project_path(project_root)
    target = ensure_path_in_project(root, Path(relative_path))

    if not target.exists():
        raise FileNotFoundError(f"File does not exist: {relative_path}")
    if not target.is_file():
        raise IsADirectoryError(f"Path is not a file: {relative_path}")
    if _looks_binary(target):
        raise ValueError(f"Refusing to read binary file: {relative_path}")

    try:
        with target.open("r", encoding="utf-8") as handle:
            content = handle.read(max_chars + 1)
    except UnicodeDecodeError as exc:
        raise ValueError(f"File is not valid UTF-8 text: {relative_path}") from exc

    truncated = len(content) > max_chars
    if truncated:
        content = content[:max_chars]

    return {
        "path": _relative_path(target, root),
        "content": content,
        "truncated": truncated,
        "size_chars": len(content),
    }


def _relative_path(path: Path, root: Path) -> str:
    return path.relative_to(root).as_posix()


def _looks_binary(path: Path) -> bool:
    try:
        chunk = path.read_bytes()[:BINARY_CHECK_BYTES]
    except OSError as exc:
        raise OSError(f"Could not read file for binary check: {path}") from exc
    return b"\x00" in chunk
