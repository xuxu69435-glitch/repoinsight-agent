from __future__ import annotations

from pathlib import Path
from typing import Any

from repoinsight.tools import git_tools
from repoinsight.tools.git_tools import git_diff, git_log_oneline, git_status


def test_git_status_in_non_git_repo_returns_structured_result(tmp_path: Path) -> None:
    project = tmp_path / "project"
    project.mkdir()

    result = git_status(str(project))

    assert result["command"] == "git status"
    assert result["allowed"] is True
    assert "exit_code" in result
    assert "stderr" in result


def test_git_diff_returns_structured_result(tmp_path: Path) -> None:
    project = tmp_path / "project"
    project.mkdir()

    result = git_diff(str(project), stat_only=True)

    assert result["command"] == "git diff --stat"
    assert result["allowed"] is True
    assert "stdout" in result
    assert "stderr" in result


def test_git_log_oneline_limits_max_count(monkeypatch, tmp_path: Path) -> None:
    project = tmp_path / "project"
    project.mkdir()
    output = "\n".join(f"{index:04x} message {index}" for index in range(20))

    def fake_run_safe_command(
        project_root: str,
        command: str,
        timeout_seconds: int = 60,
    ) -> dict[str, Any]:
        return {
            "command": command,
            "allowed": True,
            "exit_code": 0,
            "stdout": output,
            "stderr": "",
            "duration_seconds": 0.01,
            "timed_out": False,
            "stdout_truncated": False,
            "stderr_truncated": False,
            "timeout_seconds": timeout_seconds,
            "project_root": project_root,
        }

    monkeypatch.setattr(git_tools, "run_safe_command", fake_run_safe_command)

    result = git_log_oneline(str(project), max_count=5)

    assert result["command"] == "git log --oneline"
    assert result["max_count"] == 5
    assert len(result["stdout"].splitlines()) == 5


def test_git_log_oneline_clamps_max_count(monkeypatch, tmp_path: Path) -> None:
    project = tmp_path / "project"
    project.mkdir()

    def fake_run_safe_command(
        project_root: str,
        command: str,
        timeout_seconds: int = 60,
    ) -> dict[str, Any]:
        return {
            "command": command,
            "allowed": True,
            "exit_code": 0,
            "stdout": "a one\nb two",
            "stderr": "",
            "duration_seconds": 0.01,
            "timed_out": False,
        }

    monkeypatch.setattr(git_tools, "run_safe_command", fake_run_safe_command)

    assert git_log_oneline(str(project), max_count=0)["max_count"] == 1
    assert git_log_oneline(str(project), max_count=99)["max_count"] == 50
