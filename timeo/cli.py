"""
cli — command-line interface for inspecting and managing the timeo cache.

Usage:
    timeo cache info   [--cache user|project]
    timeo cache reset  [--cache user|project] [--before YYYY-MM-DD] [--yes]
"""

from __future__ import annotations

import sys
from datetime import datetime, timezone

import click
from rich import box
from rich.console import Console
from rich.table import Table

from timeo.cache import load_cache, prune_entries_before, resolve_cache_path

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

    for _fn_hash, entry in sorted(entries.items(), key=lambda x: x[1].name):
        table.add_row(
            entry.name,
            f"{entry.ema_duration_seconds:.2f}s",
            str(entry.run_count),
            entry.last_updated[:19].replace("T", " "),
        )

    console.print(table)
    console.print()


@cache.command("reset")
@_CACHE_OPTION
@click.option(
    "--before",
    default=None,
    metavar="YYYY-MM-DD",
    help="Only remove entries last updated before this date.",
)
@click.option(
    "--yes",
    is_flag=True,
    default=False,
    help="Skip the confirmation prompt.",
)
def cache_reset(cache: str, before: str | None, yes: bool) -> None:
    """Delete cached timing data.

    Without --before, the entire cache is deleted.
    With --before YYYY-MM-DD, only entries older than that date are removed.
    """
    try:
        path = resolve_cache_path(cache)
    except ValueError as e:
        console.print(f"[red]Error:[/red] {e}")
        sys.exit(1)

    # Parse --before date if provided.
    cutoff: datetime | None = None
    if before is not None:
        try:
            cutoff = datetime.strptime(before, "%Y-%m-%d").replace(tzinfo=timezone.utc)
        except ValueError:
            console.print(
                f"[red]Error:[/red] Invalid date {before!r}. Use YYYY-MM-DD format."
            )
            sys.exit(1)

    if not path.exists():
        console.print(
            f"[yellow]Nothing to reset — cache file does not exist:[/yellow] {path}\n"
        )
        return

    # Build confirmation prompt.
    if cutoff is not None:
        prompt_msg = (
            f"Remove all entries last updated before {before}? "
            f"This cannot be undone."
        )
    else:
        prompt_msg = "This will delete all cached timing data. Are you sure?"

    if not yes:
        click.confirm(prompt_msg, abort=True)

    # Perform the operation.
    if cutoff is not None:
        removed, remaining = prune_entries_before(cutoff, cache_path=path)
        if removed == 0:
            console.print(f"[yellow]No entries found before {before}.[/yellow]\n")
        else:
            console.print(
                f"[green]✓[/green] Removed [bold]{removed}[/bold] "
                f"entr{'y' if removed == 1 else 'ies'} "
                f"({remaining} remaining).\n"
            )
    else:
        path.unlink()
        console.print(f"[green]✓[/green] Cache reset: {path}\n")
