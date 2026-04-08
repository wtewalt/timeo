# Step 7: Learn Mode (`learn=True`)

## Goal
Integrate the timing cache into the `@timeo.track` decorator via the opt-in `learn=True` flag. When enabled, the progress bar is driven by elapsed time against the EMA estimate instead of discrete steps.

## Tasks

### 1. Update `track` to accept `learn=True`
The decorator must support both bare and parameterized usage:

```python
@timeo.track              # standard step-based mode (unchanged)
@timeo.track(learn=True)  # time-based EMA mode
```

Implement this by making `track` detect whether it was called with arguments:

```python
def track(fn=None, *, learn: bool = False):
    def decorator(fn):
        @functools.wraps(fn)
        def wrapper(*args, **kwargs):
            ...
        return wrapper

    if fn is not None:
        # used as @timeo.track (no parentheses)
        return decorator(fn)
    # used as @timeo.track(...) with arguments
    return decorator
```

### 2. Learn mode behavior in the wrapper

When `learn=True`:

1. Compute `fn_hash = hash_function(fn)` (from `timeo.hashing`).
2. Call `get_entry(fn_hash)` (from `timeo.cache`).
3. If no entry exists (first run):
   - Create a `TrackedTask` with `total=None` and `name=f"{fn.__name__} (learning...)"`.
   - Proceed as a normal indeterminate bar.
4. If an entry exists:
   - Create a `TrackedTask` with `total=None` (total is not step-based in learn mode) and store `ema_duration_seconds` on the task for use by the manager.
   - The manager will drive the bar using elapsed time (see below).
5. After the function returns (in `finally`):
   - Call `update_entry(fn_hash, fn.__qualname__, elapsed)` to update the cache with the actual duration.

### 3. Update `TrackedTask` for learn mode
Add two optional fields to `TrackedTask`:

| Field | Type | Description |
|---|---|---|
| `learn` | `bool` | Whether this task is in learn mode (`False` by default) |
| `ema_duration_seconds` | `float \| None` | The EMA estimate for this task, if known (`None` on first run) |

### 4. Update `ProgressManager` to handle time-driven bars

In `start_task`, detect if `task.learn is True`:
- If `task.ema_duration_seconds` is `None` (first run): register as an indeterminate spinner task with the label `"{name} (learning...)"`.
- If `task.ema_duration_seconds` is set: register as a determinate task with `total=1000` (use integer steps as a proxy for time — the manager will advance it based on elapsed time).

Add a background tick to the manager (e.g., using a `threading.Thread` or by hooking into `rich`'s refresh cycle) that periodically updates time-driven tasks:

```python
# on each tick for learn-mode tasks with a known EMA:
elapsed = time.perf_counter() - task.start_time
fraction = min(elapsed / task.ema_duration_seconds, 0.99)
progress.update(task.rich_task_id, completed=int(fraction * 1000))
```

The bar stalls at 99% (`0.99`) if the function overruns the estimate. It jumps to 100% only in `finish_task` when the function actually returns.

### 5. Add `start_time` field to `TrackedTask`
Record `time.perf_counter()` when the task is created so the manager can compute elapsed time on each tick.

## Notes
- The tick interval for updating time-driven bars should be ~100ms (10 Hz). This keeps the bar smooth without excessive CPU usage.
- The background tick thread should be a daemon thread so it does not prevent process exit.
- `fn.__qualname__` is preferred over `fn.__name__` for the cache's human-readable `name` field as it includes the class name for methods.

## Acceptance Criteria
- `@timeo.track(learn=True)` works without errors.
- `@timeo.track` (no args) still works exactly as before.
- First run shows an indeterminate bar labeled `"my_func (learning...)"`.
- Subsequent runs show a time-driven determinate bar that fills over the EMA duration.
- A function that overruns the estimate stalls at ~99% until it returns.
- The cache is updated after every run (first and subsequent).
- Changing the function body causes the cache to miss and the "learning..." bar to reappear.
- mypy passes with no errors on all modified files.
