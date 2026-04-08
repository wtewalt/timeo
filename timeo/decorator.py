"""
track decorator, advance(), and iter() — the primary user-facing API for timeo.
"""

from __future__ import annotations

import functools
import time
from collections.abc import Generator, Iterable, Sized
from contextvars import ContextVar
from typing import Any, Callable, TypeVar

from timeo.manager import ProgressManager
from timeo.task import TrackedTask

# ---------------------------------------------------------------------------
# ContextVar — holds the currently-executing TrackedTask for this context
# ---------------------------------------------------------------------------

_current_task: ContextVar[TrackedTask | None] = ContextVar(
    "_current_task", default=None
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

F = TypeVar("F", bound=Callable[..., Any])


def _infer_total(*args: Any, **kwargs: Any) -> int | None:
    """Return len() of the first Sized argument, or None if none found."""
    for arg in args:
        if isinstance(arg, Sized):
            return len(arg)
    for arg in kwargs.values():
        if isinstance(arg, Sized):
            return len(arg)
    return None


# ---------------------------------------------------------------------------
# track decorator
# ---------------------------------------------------------------------------


def track(fn: F | None = None, *, learn: bool = False) -> Any:
    """Decorator that wraps a function with a live terminal progress bar.

    Usage::

        @timeo.track
        def process(items):
            for item in timeo.iter(items):
                ...

        @timeo.track(learn=True)
        def run_pipeline(data):
            ...
    """

    def decorator(func: F) -> F:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            total = _infer_total(*args, **kwargs)
            task = TrackedTask(
                name=func.__name__,
                total=total,
                learn=learn,
            )

            manager = ProgressManager.get()
            manager.start_task(task)

            token = _current_task.set(task)
            start = time.perf_counter()
            try:
                return func(*args, **kwargs)
            finally:
                elapsed = time.perf_counter() - start
                _current_task.reset(token)
                manager.finish_task(task, elapsed=elapsed)

        return wrapper  # type: ignore[return-value]

    if fn is not None:
        # Used as @timeo.track (no parentheses)
        return decorator(fn)
    # Used as @timeo.track(...) with arguments
    return decorator


# ---------------------------------------------------------------------------
# advance() and iter()
# ---------------------------------------------------------------------------


def advance(amount: int = 1) -> None:
    """Advance the current tracked task by the given number of steps.

    No-ops silently if called outside a tracked function.
    """
    task = _current_task.get()
    if task is None:
        return
    ProgressManager.get().advance_task(task, amount)


def iter(iterable: Iterable[Any]) -> Generator[Any, None, None]:
    """Iterate over items and automatically advance the progress bar each step."""
    for item in iterable:
        yield item
        advance()
