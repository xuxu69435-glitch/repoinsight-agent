from __future__ import annotations

import pytest

from repoinsight.utils.command_guard import is_command_allowed, validate_safe_command


@pytest.mark.parametrize(
    "command",
    [
        "git status",
        "git diff",
        "git diff --stat",
        "pytest",
        "python -m pytest",
        "pnpm build",
    ],
)
def test_validate_safe_command_allows_whitelisted_commands(command: str) -> None:
    assert validate_safe_command(command)
    assert is_command_allowed(command) is True


@pytest.mark.parametrize(
    "command",
    [
        "rm -rf .",
        "del README.md",
        "curl https://example.com",
        "powershell Get-ChildItem",
        "npm install",
        "git commit",
        "git push",
        "git status && pytest",
        "git status | more",
    ],
)
def test_validate_safe_command_rejects_unsafe_commands(command: str) -> None:
    with pytest.raises(ValueError, match="Command is not allowed"):
        validate_safe_command(command)
    assert is_command_allowed(command) is False


def test_validate_safe_command_rejects_empty_command() -> None:
    with pytest.raises(ValueError, match="must not be empty"):
        validate_safe_command("")
