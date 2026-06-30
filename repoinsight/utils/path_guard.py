"""Path validation helpers for safe local repository access."""

from __future__ import annotations

import os
from pathlib import Path


def resolve_project_path(project_path: str) -> Path:
    """Return an absolute project path after validating that it exists."""
    if not project_path or not project_path.strip():
        raise ValueError("Project path must not be empty.")

    path = Path(project_path).expanduser()
    try:
        resolved = path.resolve(strict=True)
    except FileNotFoundError as exc:
        raise FileNotFoundError(f"Project path does not exist: {project_path}") from exc

    if not resolved.is_dir():
        raise NotADirectoryError(f"Project path is not a directory: {resolved}")

    return resolved


def ensure_path_in_project(project_root: Path, target_path: Path) -> Path:
    """Resolve a target path and ensure it stays inside project_root."""
    root = project_root.expanduser().resolve(strict=True)
    if not root.is_dir():
        raise NotADirectoryError(f"Project root is not a directory: {root}")

    candidate = target_path.expanduser()
    if not candidate.is_absolute():
        candidate = root / candidate

    resolved = candidate.resolve(strict=False)
    if not _is_relative_to(resolved, root):
        raise PermissionError(f"Path '{resolved}' is outside project root '{root}'.")

    return resolved


def _is_relative_to(candidate: Path, root: Path) -> bool:
    candidate_path = os.path.normcase(os.path.abspath(str(candidate)))
    root_path = os.path.normcase(os.path.abspath(str(root)))
    try:
        return os.path.commonpath([candidate_path, root_path]) == root_path
    except ValueError:
        return False
