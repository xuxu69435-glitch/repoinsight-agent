"""LangChain tool wrappers for safe repository analysis."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from langchain_core.tools import BaseTool, StructuredTool

from repoinsight.analyzers.project_detector import detect_project
from repoinsight.config import (
    DEFAULT_MAX_DEPTH,
    DEFAULT_MAX_FILE_CHARS,
    DEFAULT_MAX_SEARCH_RESULTS,
)
from repoinsight.tools.command_tools import run_safe_command
from repoinsight.tools.file_tools import list_files, read_file
from repoinsight.tools.git_tools import git_diff, git_log_oneline, git_status
from repoinsight.tools.report_tools import write_report, write_structured_report
from repoinsight.tools.search_tools import search_code


def create_repo_tools(project_root: Path) -> list[BaseTool]:
    """Create LangChain tools with project_root bound in a closure."""
    root = project_root.resolve()

    def list_project_files(max_depth: int = DEFAULT_MAX_DEPTH) -> dict[str, Any]:
        """List the project directory structure without reading file contents."""
        return list_files(str(root), max_depth=max_depth)

    def read_project_file(
        relative_path: str,
        max_chars: int = DEFAULT_MAX_FILE_CHARS,
    ) -> dict[str, Any]:
        """Read a UTF-8 text file inside the project by relative path."""
        return read_file(str(root), relative_path=relative_path, max_chars=max_chars)

    def search_project_code(
        query: str,
        max_results: int = DEFAULT_MAX_SEARCH_RESULTS,
    ) -> dict[str, Any]:
        """Search project text files for a literal query and return matching lines."""
        return search_code(str(root), query=query, max_results=max_results)

    def write_markdown_report(filename: str, content: str) -> dict[str, Any]:
        """Write a Markdown report into the project's reports directory."""
        return write_report(str(root), filename=filename, content=content)

    def write_structured_analysis_report(
        filename: str,
        report: dict[str, Any],
    ) -> dict[str, Any]:
        """Write the final structured report as both Markdown and JSON.

        The report must match the AnalysisReport schema. The tool writes
        reports/<base>.md and reports/<base>.json and is the preferred final
        report tool for RepoInsight Agent.
        """
        return write_structured_report(str(root), filename=filename, report=report)

    def run_project_command(
        command: str,
        timeout_seconds: int = 60,
    ) -> dict[str, Any]:
        """Run a command only if it matches the safe whitelist policy.

        This tool cannot install dependencies, execute arbitrary shell syntax,
        delete files, commit, push, reset, or clean Git state. It uses
        shell=False and returns stdout, stderr, exit code, timeout, and
        truncation metadata.
        """
        return run_safe_command(str(root), command=command, timeout_seconds=timeout_seconds)

    def get_git_status() -> dict[str, Any]:
        """Return git status output for the selected project."""
        return git_status(str(root))

    def get_git_diff(stat_only: bool = False) -> dict[str, Any]:
        """Return git diff output, or git diff --stat when stat_only is true."""
        return git_diff(str(root), stat_only=stat_only)

    def get_git_log(max_count: int = 10) -> dict[str, Any]:
        """Return recent git log --oneline entries, limited to 1-50 lines."""
        return git_log_oneline(str(root), max_count=max_count)

    def detect_project_profile() -> dict[str, Any]:
        """Detect project type, stack, entry points, scripts, and config files."""
        return detect_project(str(root))

    return [
        StructuredTool.from_function(
            func=detect_project_profile,
            name="detect_project_profile",
            description=(
                "Detect the project profile without calling an LLM or running commands. "
                "Returns project types, languages, frameworks, dependencies, scripts, "
                "entry points, config files, evidence files, confidence, and notes."
            ),
        ),
        StructuredTool.from_function(
            func=list_project_files,
            name="list_project_files",
            description=(
                "List the project directory structure. Use this first before reading files."
            ),
        ),
        StructuredTool.from_function(
            func=read_project_file,
            name="read_project_file",
            description=(
                "Read one UTF-8 text file by project-relative path. "
                "Use this after identifying key files."
            ),
        ),
        StructuredTool.from_function(
            func=search_project_code,
            name="search_project_code",
            description="Search project code for a literal query and return file, line, and text.",
        ),
        StructuredTool.from_function(
            func=write_markdown_report,
            name="write_markdown_report",
            description="Write the final Markdown report as project_root/reports/<filename>.",
        ),
        StructuredTool.from_function(
            func=write_structured_analysis_report,
            name="write_structured_analysis_report",
            description=(
                "Preferred final report tool. Write an AnalysisReport schema dict as both "
                "Markdown and JSON under project_root/reports using the same base filename."
            ),
        ),
        StructuredTool.from_function(
            func=run_project_command,
            name="run_project_command",
            description=(
                "Run a safe whitelist command in the project root. Allowed examples include "
                "git status, git diff, pytest, python -m pytest, npm test, npm run build, "
                "pnpm build, and yarn build. Dependency installation, arbitrary shell syntax, "
                "file deletion, and Git commit/push/reset/clean are not allowed."
            ),
        ),
        StructuredTool.from_function(
            func=get_git_status,
            name="get_git_status",
            description="Run git status in the project root and return structured output.",
        ),
        StructuredTool.from_function(
            func=get_git_diff,
            name="get_git_diff",
            description="Run git diff or git diff --stat in the project root.",
        ),
        StructuredTool.from_function(
            func=get_git_log,
            name="get_git_log",
            description="Run git log --oneline and return up to max_count recent entries.",
        ),
    ]
