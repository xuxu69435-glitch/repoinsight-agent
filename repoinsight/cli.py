"""Command line interface for RepoInsight Agent."""

from __future__ import annotations

from pathlib import Path, PurePosixPath
from typing import Any

import typer
from rich.console import Console
from rich.panel import Panel
from rich.tree import Tree

from repoinsight import __version__
from repoinsight.agent.builder import build_agent
from repoinsight.config import DEFAULT_MAX_DEPTH, load_config
from repoinsight.tools.file_tools import list_files
from repoinsight.utils.path_guard import resolve_project_path

app = typer.Typer(
    help="Local repository analysis tools powered by a LangChain Agent.",
    no_args_is_help=True,
)
console = Console()


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
        agent = build_agent(root, config)
        result = agent.invoke({"messages": [{"role": "user", "content": question}]})
    except Exception as exc:
        console.print(f"[red]Agent failed:[/red] {exc}")
        raise typer.Exit(code=1) from exc

    reports_dir = root / "reports"
    report_path = _find_latest_report(reports_dir)
    console.print("[green]Agent finished.[/green]")
    console.print(f"Report directory: {reports_dir}")
    if report_path is not None:
        console.print(f"Report path: {report_path}")
    else:
        console.print("[yellow]Report path: no Markdown report was found.[/yellow]")
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


def _find_latest_report(reports_dir: Path) -> Path | None:
    if not reports_dir.exists():
        return None
    reports = [path for path in reports_dir.glob("*.md") if path.is_file()]
    if not reports:
        return None
    return max(reports, key=lambda path: path.stat().st_mtime)


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


if __name__ == "__main__":
    app()
