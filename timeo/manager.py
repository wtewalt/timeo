"""
ProgressManager — singleton coordinating the rich live display and all tracked tasks.
"""

from __future__ import annotations

import time
import threading
from contextlib import contextmanager
from typing import Generator

from rich.live import Live
from rich.progress import (
    BarColumn,
    Progress,
    TaskProgressColumn,
    TextColumn,
    TimeElapsedColumn,
)

from timeo.task import TrackedTask

_TICK_INTERVAL: float = 0.1  # seconds between learn-mode bar updates (10 Hz)
_LEARN_TOTAL: int = 1000  # proxy "steps" used for time-driven bars


def _make_progress() -> Progress:
    return Progress(
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TaskProgressColumn(),
        TimeElapsedColumn(),
        transient=False,
    )


class ProgressManager:
    """Singleton that owns the rich live display and manages active tasks."""

    _instance: ProgressManager | None = None
    _lock: threading.Lock = threading.Lock()

    def __init__(self) -> None:
        self._progress: Progress = _make_progress()
        self._live: Live = Live(self._progress, refresh_per_second=10)
        self._tasks: dict[int, TrackedTask] = {}
        self._ref_count: int = 0
        self._display_running: bool = False
        self._explicit_managed: bool = False
        self._internal_lock: threading.Lock = threading.Lock()
        self._ticker: threading.Thread | None = None
        self._ticker_stop: threading.Event = threading.Event()

    @classmethod
    def get(cls) -> ProgressManager:
        """Return the singleton instance, creating it if necessary."""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = cls()
        return cls._instance

    # ------------------------------------------------------------------
    # Display lifecycle
    # ------------------------------------------------------------------

    def _start_display(self) -> None:
        """Start the live display and background ticker if not already running."""
        if not self._display_running:
            self._live.start()
            self._display_running = True
            self._ticker_stop.clear()
            self._ticker = threading.Thread(
                target=self._tick_loop, daemon=True, name="timeo-ticker"
            )
            self._ticker.start()

    def _stop_display(self) -> None:
        """Stop the background ticker and live display."""
        if self._display_running:
            self._ticker_stop.set()
            self._live.stop()
            self._display_running = False
            # Reset progress and live so the next run starts fresh.
            self._progress = _make_progress()
            self._live = Live(self._progress, refresh_per_second=10)

    def _tick_loop(self) -> None:
        """Background thread: advance time-driven learn-mode bars on each tick."""
        while not self._ticker_stop.wait(timeout=_TICK_INTERVAL):
            with self._internal_lock:
                for task in list(self._tasks.values()):
                    if (
                        task.learn
                        and task.ema_duration_seconds is not None
                        and task.start_time is not None
                        and task.rich_task_id is not None
                        and not task.done
                    ):
                        elapsed = time.perf_counter() - task.start_time
                        fraction = min(elapsed / task.ema_duration_seconds, 0.99)
                        self._progress.update(
                            task.rich_task_id,
                            completed=int(fraction * _LEARN_TOTAL),
                        )

    # ------------------------------------------------------------------
    # Task management
    # ------------------------------------------------------------------

    def start_task(self, task: TrackedTask) -> None:
        """Register a task with the display and start it."""
        with self._internal_lock:
            self._start_display()
            task.start_time = time.perf_counter()

            if task.learn and task.ema_duration_seconds is not None:
                # Time-driven bar: use _LEARN_TOTAL proxy steps, start at 0.
                rich_id = self._progress.add_task(
                    description=task.name,
                    total=_LEARN_TOTAL,
                    completed=0,
                )
            else:
                # Step-based or indeterminate bar.
                rich_id = self._progress.add_task(
                    description=task.name,
                    total=task.total,
                    completed=task.completed,
                )

            task.rich_task_id = rich_id
            self._tasks[rich_id] = task
            self._ref_count += 1

    def finish_task(self, task: TrackedTask, elapsed: float) -> None:
        """Mark a task complete, collapse its bar, and tear down if last task."""
        with self._internal_lock:
            task.done = True
            task.elapsed = elapsed

            if task.rich_task_id is not None:
                # Strip the "(learning...)" suffix for the summary line.
                display_name = task.name.removesuffix(" (learning...)")
                summary = f"[green]✓[/green] {display_name}  [dim]{elapsed:.1f}s[/dim]"

                if task.learn:
                    final_total = _LEARN_TOTAL
                else:
                    final_total = task.total if task.total is not None else 1

                self._progress.update(
                    task.rich_task_id,
                    description=summary,
                    completed=final_total,
                    total=final_total,
                )
                self._tasks.pop(task.rich_task_id, None)

            self._ref_count = max(0, self._ref_count - 1)

            if self._ref_count == 0 and not self._explicit_managed:
                self._stop_display()

    def advance_task(self, task: TrackedTask, amount: int = 1) -> None:
        """Advance a task's progress by the given amount."""
        task.advance(amount)
        if task.rich_task_id is not None:
            self._progress.update(task.rich_task_id, advance=amount)

    def update_task_description(self, task: TrackedTask, description: str) -> None:
        """Update the display description of a task."""
        if task.rich_task_id is not None:
            self._progress.update(task.rich_task_id, description=description)

    def update_task_time(self, task: TrackedTask, completed: int) -> None:
        """Set a task's completed value directly (used by learn-mode ticking)."""
        if task.rich_task_id is not None:
            self._progress.update(task.rich_task_id, completed=completed)

    # ------------------------------------------------------------------
    # timeo.live() context manager
    # ------------------------------------------------------------------

    @contextmanager
    def live(self) -> Generator[None, None, None]:
        """Context manager for explicit display lifecycle control."""
        with self._internal_lock:
            self._explicit_managed = True
            self._start_display()
        try:
            yield
        finally:
            with self._internal_lock:
                self._explicit_managed = False
                self._stop_display()
