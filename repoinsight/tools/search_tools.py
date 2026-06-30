"""Code search tools with ripgrep first and a Python fallback."""

from __future__ import annotations

import os
import re
import shutil
import subprocess
from pathlib import Path
from typing import Any

from repoinsight.config import IGNORED_DIRECTORIES
from repoinsight.tools.file_tools import BINARY_CHECK_BYTES
from repoinsight.utils.path_guard import resolve_project_path


def search_code(project_root: str, query: str, max_results: int = 50) -> dict[str, Any]:
    """Search for a literal query in project text files."""
    if not query:
        raise ValueError("query must not be empty.")
    if max_results <= 0:
        raise ValueError("max_results must be greater than 0.")

    root = resolve_project_path(project_root)
    rg_path = shutil.which("rg")
    if rg_path:
        matches = _search_with_rg(root, query, max_results, rg_path)
    else:
        matches = _search_with_python(root, query, max_results)

    return {"root": str(root), "query": query, "matches": matches}


def _search_with_rg(root: Path, query: str, max_results: int, rg_path: str) -> list[dict[str, Any]]:
    command = [
        rg_path,
        "--line-number",
        "--color",
        "never",
        "--no-heading",
        "--fixed-strings",
    ]
    for ignored in sorted(IGNORED_DIRECTORIES):
        command.extend(["--glob", f"!{ignored}/**"])
    command.extend([query, "."])

    result = subprocess.run(
        command,
        cwd=root,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    if result.returncode not in {0, 1}:
        raise RuntimeError(f"ripgrep search failed: {result.stderr.strip()}")

    matches: list[dict[str, Any]] = []
    for line in result.stdout.splitlines():
        parsed = _parse_rg_line(line)
        if parsed is None:
            continue
        matches.append(parsed)
        if len(matches) >= max_results:
            break
    return matches


def _search_with_python(root: Path, query: str, max_results: int) -> list[dict[str, Any]]:
    matches: list[dict[str, Any]] = []
    for current, dirnames, filenames in os.walk(root):
        dirnames[:] = sorted(name for name in dirnames if name not in IGNORED_DIRECTORIES)
        for filename in sorted(filenames):
            path = Path(current) / filename
            if not _is_text_file(path):
                continue
            try:
                with path.open("r", encoding="utf-8") as handle:
                    for line_number, line in enumerate(handle, start=1):
                        if query in line:
                            matches.append(
                                {
                                    "file": path.relative_to(root).as_posix(),
                                    "line": line_number,
                                    "text": line.rstrip("\n\r"),
                                }
                            )
                            if len(matches) >= max_results:
                                return matches
            except (OSError, UnicodeDecodeError):
                continue
    return matches


def _parse_rg_line(line: str) -> dict[str, Any] | None:
    match = re.match(r"^(.*?):(\d+):(.*)$", line)
    if not match:
        return None
    file_path = match.group(1).replace("\\", "/")
    if file_path.startswith("./"):
        file_path = file_path[2:]
    return {"file": file_path, "line": int(match.group(2)), "text": match.group(3)}


def _is_text_file(path: Path) -> bool:
    try:
        chunk = path.read_bytes()[:BINARY_CHECK_BYTES]
    except OSError:
        return False
    if b"\x00" in chunk:
        return False
    try:
        chunk.decode("utf-8")
    except UnicodeDecodeError:
        return False
    return True
