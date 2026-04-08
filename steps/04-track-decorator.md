# Step 4: `@timeo.track` Decorator

## Goal
Implement `timeo/decorator.py` — the `@timeo.track` decorator that wraps a function, infers `total` from its arguments, registers it with the `ProgressManager`, and manages the `ContextVar` lifecycle.

## Tasks

### 1. Set up the `ContextVar`
Define a module-level `ContextVar` in `decorator.py` (or a shared `_context.py` module) to hold the currently-executing `TrackedTask`:

```python
from contextvars import ContextVar
from timeo.task import TrackedTask

_current_task: ContextVar[TrackedTask | None] = ContextVar("_current_task", default=None)
```

This will be used by `timeo.advance()` to know which task to update.

### 2. Implement `total` inference
Write a helper that inspects the positional and keyword arguments passed to a decorated function and returns the `len()` of the first `Sized` argument found, or `None` if none exists:

```python
def _infer_total(*args, **kwargs) -> int | None:
    ...
```

Use `collections.abc.Sized` for the `isinstance` check.

### 3. Implement the `track` decorator
The decorator should:

1. Accept the decorated function and return a wrapper.
2. When the wrapper is called:
   - Call `_infer_total` with the actual arguments to determine `total`.
   - Create a `TrackedTask(name=fn.__name__, total=total)`.
   - Call `ProgressManager.get().start_task(task)`.
   - Push `task` onto `_current_task` using `_current_task.set(task)`, saving the token for later reset.
   - Call the original function inside a `try/finally`:
     - On completion (or exception): reset `_current_task` to its previous value using the saved token, call `ProgressManager.get().finish_task(task, elapsed=...)`, measure elapsed time with `time.perf_counter`.
3. Return the original function's return value.

```python
import functools

def track(fn):
    @functools.wraps(fn)
    def wrapper(*args, **kwargs):
        ...
    return wrapper
```

### 4. Implement `timeo.advance()`
In `decorator.py` (or `__init__.py`), implement the `advance()` function:

```python
def advance(amount: int = 1) -> None:
    task = _current_task.get()
    if task is None:
        return  # called outside a tracked function, silently no-op
    ProgressManager.get().advance_task(task, amount)
```

### 5. Implement `timeo.iter()`
A generator wrapper that advances the current task on each iteration:

```python
def iter(iterable):
    for item in iterable:
        yield item
        advance()
```

## Notes
- Use `functools.wraps` to preserve the wrapped function's `__name__`, `__doc__`, etc.
- Use `time.perf_counter()` for elapsed time measurement (higher resolution than `time.time()`).
- `advance()` should silently no-op if called outside a tracked function (i.e., `_current_task.get()` returns `None`) rather than raising an error.

## Acceptance Criteria
- `@timeo.track` can be applied to any function.
- Running a decorated function shows a progress bar in the terminal.
- `timeo.advance()` correctly increments the active task's progress.
- `timeo.iter()` auto-advances on each iteration without manual `advance()` calls.
- `_infer_total` correctly returns `len()` of the first `Sized` argument, or `None`.
- `_current_task` is correctly reset after the function returns (including on exception).
- mypy passes with no errors on this file.
