"""Command line interface for RepoInsight Agent."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Any

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.tree import Tree

from repoinsight import __version__
from repoinsight.analyzers.project_detector import detect_project
from repoinsight.config import DEFAULT_MAX_DEPTH, load_config
from repoinsight.tools.file_tools import list_files
from repoinsight.utils.path_guard import resolve_project_path
from repoinsight.utils.report_guard import (
    ReportWriteError,
    ensure_report_file_writable,
    ensure_reports_dir,
)

app = typer.Typer(
    help="Local repository analysis tools powered by a LangChain Agent.",
    no_args_is_help=True,
)
console = Console()
WORKFLOW_CLI_API_KEY_ERROR = (
    "OPENAI_API_KEY is required for --with-llm. "
    "Use --no-llm for deterministic workflow."
)


@dataclass(frozen=True)
class DoctorCheck:
    name: str
    status: str
    detail: str


@app.command()
def version() -> None:
    """Print the current version."""
    console.print(__version__)


@app.command()
def scan(
    path: str = typer.Option(..., "--path", "-p", help="Local project path to scan."),
    max_depth: int = typer.Option(
        DEFAULT_MAX_DEPTH,
        "--max-depth",
        help="Maximum directory depth to display.",
    ),
) -> None:
    """Validate a project path and print its basic directory structure."""
    root = resolve_project_path(path)
    structure = list_files(str(root), max_depth=max_depth)

    console.print(Panel.fit(f"Project: {root}", title="RepoInsight Scan"))
    console.print(_build_tree(structure))
    console.print(
        f"[dim]{structure['total_directories']} directories, "
        f"{structure['total_files']} files[/dim]"
    )


@app.command()
def profile(
    path: str = typer.Option(..., "--path", "-p", help="Local project path to profile."),
    json_output: bool = typer.Option(
        False,
        "--json",
        help="Output the project profile as JSON.",
    ),
) -> None:
    """Detect project type, stack, entry points, and config files without an LLM."""
    root = resolve_project_path(path)
    detected = detect_project(str(root))
    if json_output:
        console.print(json.dumps(detected, ensure_ascii=False, indent=2))
        return

    console.print(Panel.fit(f"Project: {root}", title="RepoInsight Profile"))
    console.print(_build_profile_table(detected))


@app.command()
def doctor(
    path: str = typer.Option(..., "--path", "-p", help="Local project path to check."),
) -> None:
    """Check local RepoInsight prerequisites and report write readiness."""
    checks = _run_doctor_checks(path)
    console.print(_build_doctor_table(checks))
    if any(check.status == "FAIL" for check in checks):
        raise typer.Exit(code=1)


@app.command()
def workflow(
    task: str = typer.Argument(..., help="Analysis task for the workflow."),
    path: str = typer.Option(..., "--path", "-p", help="Local project path to analyze."),
    no_llm: bool = typer.Option(
        True,
        "--no-llm/--with-llm",
        help="Run deterministic workflow without LLM, or request LLM mode when available.",
    ),
) -> None:
    """Run the LangGraph workflow mode."""
    root = resolve_project_path(path)
    config = None
    if not no_llm:
        try:
            config = load_config()
        except ValueError as exc:
            console.print(f"[red]Configuration error:[/red] {exc}")
            raise typer.Exit(code=1) from exc
        if not config.openai_api_key:
            console.print(f"[red]{WORKFLOW_CLI_API_KEY_ERROR}[/red]")
            raise typer.Exit(code=1)

    from repoinsight.workflow.graph import run_workflow

    try:
        result = run_workflow(str(root), task, no_llm=no_llm, config=config)
    except ValueError as exc:
        console.print(f"[red]{exc}[/red]")
        raise typer.Exit(code=1) from exc

    profile_data = result.get("profile") or {}
    console.print("[green]Workflow finished.[/green]")
    console.print(f"Analysis mode: {result.get('analysis_mode') or '-'}")
    console.print(f"LLM used: {_format_bool(result.get('llm_used'))}")
    console.print(f"LLM model: {result.get('llm_model') or '-'}")
    console.print(f"Project types: {_join_values(profile_data.get('project_types', []))}")
    console.print(f"Languages: {_join_values(profile_data.get('languages', []))}")
    console.print(f"Frameworks: {_join_values(profile_data.get('frameworks', []))}")
    console.print(f"Markdown report path: {result.get('markdown_report_path') or '-'}")
    console.print(f"JSON report path: {result.get('json_report_path') or '-'}")
    _print_state_messages("Warnings", result.get("warnings", []), "yellow")
    _print_state_messages("Errors", result.get("errors", []), "red")
    if result.get("errors"):
        raise typer.Exit(code=1)


@app.command()
def ask(
    question: str = typer.Argument(..., help="Analysis question for the Agent."),
    path: str = typer.Option(..., "--path", "-p", help="Local project path to analyze."),
) -> None:
    """Analyze a local project with the LangChain Agent runtime."""
    root = resolve_project_path(path)
    console.print(Panel.fit(f"Project: {root}\nQuestion: {question}", title="RepoInsight Ask"))

    try:
        config = load_config()
    except ValueError as exc:
        console.print(f"[red]Configuration error:[/red] {exc}")
        raise typer.Exit(code=1) from exc

    if not config.openai_api_key:
        console.print(
            "[red]OPENAI_API_KEY is required to run the Agent.[/red]\n"
            "Copy .env.example to .env and set OPENAI_API_KEY. "
            "OPENAI_BASE_URL is optional for OpenAI-compatible providers."
        )
        raise typer.Exit(code=1)

    try:
        from repoinsight.agent.builder import build_agent

        agent = build_agent(root, config)
        result = agent.invoke({"messages": [{"role": "user", "content": question}]})
    except Exception as exc:
        console.print(f"[red]Agent failed:[/red] {exc}")
        raise typer.Exit(code=1) from exc

    reports_dir = root / "reports"
    report_paths = _extract_report_paths(result)
    console.print("[green]Agent finished.[/green]")
    console.print(f"Report directory: {reports_dir}")
    if report_paths:
        markdown_path = report_paths.get("markdown_report_path")
        json_path = report_paths.get("json_report_path")
        if markdown_path:
            console.print(f"Markdown report path: {markdown_path}")
        if json_path:
            console.print(f"JSON report path: {json_path}")
    else:
        console.print("[yellow]Report path: no explicit report path was returned.[/yellow]")
        console.print("Check the reports directory for generated files.")
    console.print(f"Answer preview: {_extract_answer_preview(result)}")


def _build_tree(structure: dict[str, Any]) -> Tree:
    root = Path(str(structure["root"]))
    tree = Tree(f"[bold]{root.name or str(root)}[/bold]")
    nodes: dict[str, Tree] = {"": tree}

    directories = sorted(
        (str(item) for item in structure["directories"]),
        key=lambda value: (value.count("/"), value.lower()),
    )
    for directory in directories:
        path = PurePosixPath(directory)
        parent_key = "" if str(path.parent) == "." else path.parent.as_posix()
        parent = nodes.get(parent_key, tree)
        nodes[directory] = parent.add(f"[bold cyan]{path.name}/[/bold cyan]")

    files = sorted(
        (str(item) for item in structure["files"]),
        key=lambda value: (value.count("/"), value.lower()),
    )
    for file_path in files:
        path = PurePosixPath(file_path)
        parent_key = "" if str(path.parent) == "." else path.parent.as_posix()
        parent = nodes.get(parent_key, tree)
        parent.add(path.name)

    return tree


def _build_profile_table(profile_data: dict[str, Any]) -> Table:
    table = Table(title="Project Profile", show_header=True, header_style="bold")
    table.add_column("Field", style="cyan", no_wrap=True)
    table.add_column("Value")

    table.add_row("Project Types", _join_values(profile_data.get("project_types", [])))
    table.add_row("Languages", _join_values(profile_data.get("languages", [])))
    table.add_row("Frameworks", _join_values(profile_data.get("frameworks", [])))
    table.add_row("Package Managers", _join_values(profile_data.get("package_managers", [])))
    table.add_row("Entry Points", _format_path_items(profile_data.get("entry_points", [])))
    table.add_row("Key Config Files", _format_path_items(profile_data.get("config_files", [])))
    table.add_row("Scripts", _format_scripts(profile_data.get("scripts", [])))
    table.add_row("Confidence", str(profile_data.get("confidence", 0)))
    return table


def _run_doctor_checks(path: str) -> list[DoctorCheck]:
    checks: list[DoctorCheck] = []
    try:
        root = resolve_project_path(path)
    except (ValueError, FileNotFoundError, NotADirectoryError) as exc:
        checks.append(DoctorCheck("Project path", "FAIL", str(exc)))
        _append_environment_checks(checks, None)
        return checks

    checks.append(DoctorCheck("Project path", "OK", str(root)))
    _append_reports_checks(checks, root)
    _append_environment_checks(checks, root)
    return checks


def _append_reports_checks(checks: list[DoctorCheck], root: Path) -> None:
    reports_dir = root / "reports"
    existed = reports_dir.exists()
    try:
        ensured = ensure_reports_dir(root)
    except ReportWriteError as exc:
        checks.append(DoctorCheck("Reports directory", "FAIL", str(exc)))
        checks.append(DoctorCheck("Reports writable", "FAIL", str(exc)))
        return

    action = "exists" if existed else "created"
    checks.append(DoctorCheck("Reports directory", "OK", f"{action}: {ensured}"))
    checks.append(DoctorCheck("Reports writable", "OK", str(ensured)))
    _append_workflow_report_file_check(checks, ensured)


def _append_environment_checks(checks: list[DoctorCheck], root: Path | None) -> None:
    _append_env_file_check(checks, root)
    api_key_configured = bool(os.environ.get("OPENAI_API_KEY"))
    checks.append(
        DoctorCheck(
            "OPENAI_API_KEY",
            "OK" if api_key_configured else "WARN",
            f"configured: {'yes' if api_key_configured else 'no'}",
        )
    )

    rg_path = shutil.which("rg") or shutil.which("ripgrep")
    checks.append(
        DoctorCheck(
            "ripgrep",
            "OK" if rg_path else "WARN",
            rg_path or "rg/ripgrep was not found on PATH.",
        )
    )

    git_path = shutil.which("git")
    checks.append(
        DoctorCheck(
            "git",
            "OK" if git_path else "WARN",
            git_path or "git was not found on PATH.",
        )
    )
    _append_git_repository_check(checks, root, git_path)

    checks.append(DoctorCheck("Python version", "OK", sys.version.split()[0]))
    checks.append(DoctorCheck("RepoInsight version", "OK", __version__))


def _append_workflow_report_file_check(checks: list[DoctorCheck], reports_dir: Path) -> None:
    for filename in ("workflow_analysis_report.md", "workflow_analysis_report.json"):
        report_path = reports_dir / filename
        try:
            ensure_report_file_writable(report_path)
        except ReportWriteError as exc:
            checks.append(DoctorCheck("Workflow report file", "FAIL", str(exc)))
            return
    checks.append(
        DoctorCheck(
            "Workflow report files",
            "OK",
            "default workflow report filenames are writable",
        )
    )


def _append_env_file_check(checks: list[DoctorCheck], root: Path | None) -> None:
    if root is None:
        checks.append(DoctorCheck(".env file", "WARN", "skipped because project path is invalid."))
        return
    env_path = root / ".env"
    checks.append(
        DoctorCheck(
            ".env file",
            "OK" if env_path.exists() else "WARN",
            "exists" if env_path.exists() else "not found",
        )
    )


def _append_git_repository_check(
    checks: list[DoctorCheck],
    root: Path | None,
    git_path: str | None,
) -> None:
    if root is None:
        checks.append(
            DoctorCheck("Git repository", "WARN", "skipped because project path is invalid.")
        )
        return
    if not git_path:
        checks.append(DoctorCheck("Git repository", "WARN", "skipped because git is unavailable."))
        return

    try:
        result = subprocess.run(
            [git_path, "-C", str(root), "rev-parse", "--is-inside-work-tree"],
            capture_output=True,
            check=False,
            shell=False,
            text=True,
            timeout=5,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        checks.append(DoctorCheck("Git repository", "WARN", f"could not check git: {exc}"))
        return

    if result.returncode == 0 and result.stdout.strip() == "true":
        checks.append(DoctorCheck("Git repository", "OK", "inside a git work tree"))
    else:
        detail = result.stderr.strip() or "not a git repository"
        checks.append(DoctorCheck("Git repository", "WARN", detail))


def _build_doctor_table(checks: list[DoctorCheck]) -> Table:
    table = Table(title="RepoInsight Doctor", show_header=True, header_style="bold")
    table.add_column("Check", style="cyan", no_wrap=True)
    table.add_column("Status", no_wrap=True)
    table.add_column("Detail")

    for check in checks:
        table.add_row(check.name, _format_doctor_status(check.status), check.detail)
    return table


def _format_doctor_status(status: str) -> str:
    styles = {"OK": "green", "WARN": "yellow", "FAIL": "red"}
    style = styles.get(status, "white")
    return f"[{style}]{status}[/{style}]"


def _join_values(values: list[Any]) -> str:
    if not values:
        return "-"
    return ", ".join(str(value) for value in values)


def _format_bool(value: Any) -> str:
    return "true" if value is True else "false"


def _format_path_items(items: list[dict[str, Any]]) -> str:
    if not items:
        return "-"
    return "\n".join(str(item.get("path", "-")) for item in items)


def _format_scripts(items: list[dict[str, Any]]) -> str:
    if not items:
        return "-"
    return "\n".join(f"{item.get('name', '-')}: {item.get('command', '-')}" for item in items)


def _print_state_messages(title: str, messages: list[Any], style: str) -> None:
    if not messages:
        return
    console.print(f"[{style}]{title}:[/{style}]")
    for message in messages:
        console.print(f"- {message}")


def _extract_answer_preview(result: Any, max_chars: int = 500) -> str:
    text = _extract_answer_text(result).strip()
    if not text:
        return "No answer text returned."
    if len(text) <= max_chars:
        return text
    return f"{text[:max_chars].rstrip()}..."


def _extract_answer_text(result: Any) -> str:
    if isinstance(result, dict):
        messages = result.get("messages")
        if isinstance(messages, list) and messages:
            return _message_to_text(messages[-1])
        return str(result)
    return str(result)


def _message_to_text(message: Any) -> str:
    if isinstance(message, dict):
        return _content_to_text(message.get("content", ""))
    return _content_to_text(getattr(message, "content", message))


def _content_to_text(content: Any) -> str:
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts: list[str] = []
        for item in content:
            if isinstance(item, str):
                parts.append(item)
            elif isinstance(item, dict):
                value = item.get("text") or item.get("content")
                if value:
                    parts.append(str(value))
        return "\n".join(parts)
    return str(content)


def _extract_report_paths(result: Any) -> dict[str, str]:
    found: dict[str, str] = {}

    def visit(value: Any) -> None:
        if isinstance(value, dict):
            for key in ("markdown_report_path", "json_report_path"):
                item = value.get(key)
                if isinstance(item, str) and item:
                    found[key] = item
            for item in value.values():
                visit(item)
        elif isinstance(value, list):
            for item in value:
                visit(item)

    visit(result)
    return found


if __name__ == "__main__":
    app()
