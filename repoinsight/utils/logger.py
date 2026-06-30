"""Rich console helper."""

from __future__ import annotations

from rich.console import Console

console = Console()


def get_console() -> Console:
    """Return the shared Rich console instance."""
    return console
