"""
TrackedTask — state container for a single decorated function's progress.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from rich.progress import TaskID


@dataclass
class TrackedTask:
    """Holds all progress state for one tracked function call."""

    name: str
    total: int | None = None
    completed: int = 0
    rich_task_id: TaskID | None = None
    done: bool = False
    elapsed: float | None = None
    start_time: float | None = None
    learn: bool = False
    ema_duration_seconds: float | None = None
    cache_path: Path | None = None

    def advance(self, amount: int = 1) -> None:
        """Increment completed by amount, capped at total if set."""
        if self.total is not None:
            self.completed = min(self.completed + amount, self.total)
        else:
            self.completed += amount

    @property
    def fraction_complete(self) -> float | None:
        """Return progress as a float 0.0–1.0, or None if total is unknown."""
        if self.total is None:
            return None
        if self.total == 0:
            return 1.0
        return min(self.completed / self.total, 1.0)
