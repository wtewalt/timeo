"""
track decorator, advance(), and iter() — the primary user-facing API for timeo.
"""

from __future__ import annotations

import functools
import time
from collections.abc import Generator, Iterable, Sized
from contextvars import ContextVar
from typing import Any, Callable, TypeVar

from timeo.cache import get_entry, resolve_cache_path, update_entry
from timeo.hashing import hash_function
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


def track(
    fn: F | None = None,
    *,
    learn: bool = False,
    cache: str = "user",
    depends_on: list[Callable[..., Any]] | None = None,
) -> Any:
    """Decorator that wraps a function with a live terminal progress bar.

    Args:
        learn: If ``True``, the bar is driven by an EMA of previous runtimes
               instead of discrete steps. Timing data is stored in a local
               cache and updated after every run.
        cache: Where to store timing data when ``learn=True``.
               ``"user"`` (default) stores in the platform user cache directory
               (e.g. ``~/.cache/timeo/timings.json``).
               ``"project"`` stores in ``.timeo/timings.json`` relative to the
               current working directory.
        depends_on: Optional list of callables that this function's timing
               estimate depends on.  When any listed function's bytecode
               changes, the cache key for this function changes too and
               learn-mode resets automatically.  Use this to handle cases
               where a nested/helper function changes without the decorated
               function's own bytecode changing::

                   @timeo.track(learn=True, depends_on=[helper_fn])
                   def top_function():
                       helper_fn()

               Only meaningful when ``learn=True``; ignored otherwise.

    Usage::

        @timeo.track
        def process(items):
            for item in timeo.iter(items):
                ...

        @timeo.track(learn=True)
        def run_pipeline(data):
            ...

        @timeo.track(learn=True, cache="project")
        def run_pipeline(data):
            ...

        @timeo.track(learn=True, depends_on=[helper_fn])
        def top_function():
            helper_fn()
    """

    def decorator(func: F) -> F:
        # Resolve the cache path once at decoration time so cwd() is captured
        # at the point the decorator is applied, not at each call site.
        resolved_cache_path = resolve_cache_path(cache) if learn else None

        # Pre-compute the cache key once — depends_on is fixed at decoration time.
        fn_hash = hash_function(func, depends_on=depends_on) if learn else None

        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            if learn:
                entry = get_entry(fn_hash, cache_path=resolved_cache_path)  # type: ignore[arg-type]
                if entry is None:
                    task = TrackedTask(
                        name=f"{func.__name__} (learning...)",
                        total=None,
                        learn=True,
                        ema_duration_seconds=None,
                        cache_path=resolved_cache_path,
                    )
                else:
                    task = TrackedTask(
                        name=func.__name__,
                        total=None,
                        learn=True,
                        ema_duration_seconds=entry.ema_duration_seconds,
                        cache_path=resolved_cache_path,
                    )
            else:
                total = _infer_total(*args, **kwargs)
                task = TrackedTask(
                    name=func.__name__,
                    total=total,
                    learn=False,
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
                if learn:
                    update_entry(
                        fn_hash,  # type: ignore[arg-type]
                        func.__qualname__,
                        elapsed,
                        cache_path=task.cache_path,
                    )

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
