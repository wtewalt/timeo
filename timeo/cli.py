"""
cli — command-line interface for inspecting and managing the timeo cache.

Usage:
    timeo cache info [--cache user|project]
    timeo cache reset [--cache user|project]
"""

from __future__ import annotations

import sys

import click
from rich.console import Console
from rich.table import Table
from rich import box

from timeo.cache import load_cache, resolve_cache_path

console = Console()

_CACHE_OPTION = click.option(
    "--cache",
    default="user",
    show_default=True,
    type=click.Choice(["user", "project"], case_sensitive=False),
    help="Cache location to target.",
)


@click.group()
def cli() -> None:
    """timeo — terminal progress bars via decorators.

    Manage the learn-mode timing cache from the command line.
    """


@cli.group()
def cache() -> None:
    """Inspect and manage the timeo timing cache."""


@cache.command("info")
@_CACHE_OPTION
def cache_info(cache: str) -> None:
    """Show information about the timing cache."""
    try:
        path = resolve_cache_path(cache)
    except ValueError as e:
        console.print(f"[red]Error:[/red] {e}")
        sys.exit(1)

    console.print(f"\n[bold]Cache location:[/bold] {path}")

    if not path.exists():
        console.print("[yellow]Cache file does not exist yet.[/yellow]\n")
        return

    entries = load_cache(cache_path=path)

    if not entries:
        console.print("[yellow]Cache file exists but contains no entries.[/yellow]\n")
        return

    console.print(f"[bold]Entries:[/bold] {len(entries)}\n")

    table = Table(box=box.ROUNDED, show_header=True, header_style="bold cyan")
    table.add_column("Function", style="white")
    table.add_column("EMA Duration", justify="right", style="green")
    table.add_column("Runs", justify="right", style="cyan")
    table.add_column("Last Updated", style="dim")

    for fn_hash, entry in sorted(entries.items(), key=lambda x: x[1].name):
        table.add_row(
            entry.name,
            f"{entry.ema_duration_seconds:.2f}s",
            str(entry.run_count),
            entry.last_updated[:19].replace("T", " "),  # trim to YYYY-MM-DD HH:MM:SS
        )

    console.print(table)
    console.print()


@cache.command("reset")
@_CACHE_OPTION
@click.confirmation_option(
    "--yes",
    prompt="This will delete all cached timing data. Are you sure?",
)
def cache_reset(cache: str) -> None:
    """Delete all cached timing data."""
    try:
        path = resolve_cache_path(cache)
    except ValueError as e:
        console.print(f"[red]Error:[/red] {e}")
        sys.exit(1)

    if not path.exists():
        console.print(
            f"[yellow]Nothing to reset — cache file does not exist:[/yellow] {path}\n"
        )
        return

    path.unlink()
    console.print(f"[green]✓[/green] Cache reset: {path}\n")
