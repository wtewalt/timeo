# Step 3: ProgressManager

## Goal
Implement `timeo/manager.py` — the singleton that owns the `rich` live display, manages the collection of active tasks, and controls the display lifecycle.

## Tasks

### 1. Implement `ProgressManager` as a singleton

The `ProgressManager` is the central coordinator. Only one instance should exist per process.

```python
class ProgressManager:
    _instance: "ProgressManager | None" = None

    @classmethod
    def get(cls) -> "ProgressManager":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
```

### 2. Internal state

The manager should hold:
- A `rich.progress.Progress` instance configured with appropriate columns (task name, bar, percentage, elapsed time).
- A `rich.live.Live` instance wrapping the `Progress` object.
- A list (or dict keyed by `rich_task_id`) of active `TrackedTask` instances.
- An `int` reference counter tracking how many tracked functions are currently executing.

### 3. Implement `start_task(task: TrackedTask) -> None`
- If the live display is not already running, start it.
- Register the task with `rich` via `progress.add_task()` and store the returned `TaskID` on `task.rich_task_id`.
- Increment the reference counter.

### 4. Implement `finish_task(task: TrackedTask, elapsed: float) -> None`
- Mark the task as done and record its elapsed time.
- Update the rich display to show the task as complete (collapse it to a checkmark + elapsed summary line — see Display Behavior below).
- Decrement the reference counter.
- If the reference counter reaches `0` and the display is not being managed by an explicit `timeo.live()` context manager, stop the live display.

### 5. Implement `advance_task(task: TrackedTask, amount: int = 1) -> None`
- Call `task.advance(amount)`.
- Call `progress.update(task.rich_task_id, advance=amount)` to reflect the change in the live display.

### 6. Implement `timeo.live()` context manager
Expose a context manager that gives the user explicit control over the display lifecycle:

```python
with timeo.live():
    process_files(my_files)
    download_data(my_urls)
```

When entered:
- Start the live display and set an internal flag indicating that the display is explicitly managed (so `finish_task` does not auto-stop it when the reference counter hits zero).

When exited:
- Stop the live display regardless of the reference counter.
- Clear the explicit-management flag.

### 7. Display behavior for completed tasks
When a task finishes, its full progress bar row should be replaced with a compact summary:

```
✓ process_files    12.4s
```

This can be achieved by updating the task's rich columns to show only the checkmark, name, and elapsed time.

## Notes
- Use `try/finally` discipline everywhere — the display must tear down cleanly even if an exception propagates.
- The `Progress` columns should include at minimum: task description, bar, percentage, and elapsed time. Use `rich.progress` column classes (`TextColumn`, `BarColumn`, `TaskProgressColumn`, `TimeElapsedColumn`).

## Acceptance Criteria
- `from timeo.manager import ProgressManager` works without errors.
- `ProgressManager.get()` always returns the same instance.
- Starting and finishing a task starts and stops the live display correctly.
- The reference counter prevents premature teardown when multiple tasks are active.
- `timeo.live()` context manager keeps the display alive for its duration regardless of task completions.
- mypy passes with no errors on this file.
