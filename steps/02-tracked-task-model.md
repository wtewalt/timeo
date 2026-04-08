# Step 2: TrackedTask Model

## Goal
Implement `timeo/task.py` — the dataclass that represents a single tracked function's progress state.

## Tasks

### 1. Implement `TrackedTask` in `timeo/task.py`

This is a dataclass that holds all state for one tracked function call. It should include:

| Field | Type | Description |
|---|---|---|
| `name` | `str` | Display name for the progress bar (defaults to the function's `__name__`) |
| `total` | `int \| None` | Total number of steps, or `None` if indeterminate |
| `completed` | `int` | Number of steps completed so far (starts at `0`) |
| `rich_task_id` | `TaskID \| None` | The ID assigned by `rich` when the task is registered with the live display (starts as `None`, set later by the manager) |
| `done` | `bool` | Whether the function has finished (`False` by default) |
| `elapsed` | `float \| None` | Total elapsed time in seconds once done (`None` until complete) |

### 2. Add an `advance()` method
A method that increments `completed` by a given amount (default `1`). Should not exceed `total` if `total` is set.

```python
def advance(self, amount: int = 1) -> None:
    ...
```

### 3. Add a `fraction_complete` property
Returns a `float` between `0.0` and `1.0` representing progress, or `None` if `total` is `None`.

```python
@property
def fraction_complete(self) -> float | None:
    ...
```

## Notes
- Use `@dataclass` from the standard library.
- Import `TaskID` from `rich.progress` for the type annotation.
- All fields should be type-annotated.

## Acceptance Criteria
- `from timeo.task import TrackedTask` works without errors.
- A `TrackedTask` can be instantiated with just a `name`.
- `advance()` correctly increments `completed`.
- `fraction_complete` returns `None` when `total` is `None`, and a correct fraction otherwise.
- mypy passes with no errors on this file.
