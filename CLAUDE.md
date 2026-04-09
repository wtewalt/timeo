# Timeo — Project Guide

## Overview

**Timeo** is a Python package that lets developers annotate functions with a decorator to automatically track and display their progress in the terminal. When a script runs, all decorated functions are rendered together as a collection of live progress bars using `rich`.

## Core Concept

The user imports `timeo`, applies `@timeo.track` (or similar) to any function, and when the script executes, those functions are monitored and displayed as live progress bars in the terminal — all managed automatically without the user needing to manually wire up progress bar logic.

### Example Usage

```python
import timeo

@timeo.track
def process_files(files):
    for file in files:
        handle(file)
        timeo.advance()  # or automatic via iteration hooks

@timeo.track
def download_data(urls):
    for url in urls:
        fetch(url)
        timeo.advance()

process_files(my_files)
download_data(my_urls)
```

Terminal output (while running):
```
Processing files   ━━━━━━━━━━━━━━━━━━━━━━  45% 0:00:12
Downloading data   ━━━━━━━━━━━━━━━━━━━━━━━━━━  72% 0:00:04
```

## Architecture

### Key Components

- **`timeo/decorator.py`** — The `@timeo.track` decorator. Wraps a function, registers it with the progress manager, and starts/stops tracking around the function's execution.
- **`timeo/manager.py`** — The `ProgressManager` singleton. Owns the `rich.progress.Progress` instance, maintains the registry of tracked tasks, and controls the live display lifecycle.
- **`timeo/task.py`** — Represents a single tracked task (name, total, current progress, metadata).
- **`timeo/__init__.py`** — Public API surface. Exports `track`, `advance`, and any other user-facing symbols.

### Design Principles

- **Minimal user friction** — the decorator should be the only required touchpoint.
- **Non-intrusive** — does not require users to change the internals of their functions beyond adding `timeo.advance()` calls (or wrapping iterables).
- **Composable** — multiple decorated functions should render together as a unified live display, not separate progress bars.
- **Graceful degradation** — if `total` is unknown, show a spinner or indeterminate bar rather than failing.

## Dependencies

- **`rich`** — All progress bar rendering, formatting, and live display. Use `rich.progress.Progress` with `rich.live.Live` for the unified multi-bar display.

## Releasing

### Release Process

This repo uses **[release-please](https://github.com/googleapis/release-please)** to automate versioning and changelog generation. It parses conventional commits on `main` to determine the next version and opens a release PR automatically.

- Merge the release-please PR on `main` to cut a new release.
- On release, a GitHub Actions workflow automatically builds and publishes the package to **PyPI**.
- The version in `pyproject.toml` is the source of truth and is updated by release-please.

### Conventional Commits

All commits must follow the [Conventional Commits](https://www.conventionalcommits.org/) spec since release-please relies on them to determine version bumps:

| Prefix | Effect |
|--------|--------|
| `fix:` | Patch bump |
| `feat:` | Minor bump |
| `feat!:` / `BREAKING CHANGE:` | Major bump |
| `docs:`, `chore:`, `refactor:`, etc. | No version bump |

## Development

### Setup

```bash
uv sync          # install dependencies
task dev         # or however the dev environment is activated
```

### Code Quality

This repo uses **[pre-commit](https://pre-commit.com/)** to enforce code quality on every commit. Hooks are defined in `.pre-commit-config.yaml`.

Install hooks locally (one-time):
```bash
pre-commit install
```

Hooks enforced:
- **ruff** — linting and formatting
- **mypy** — static type checking
- TOML/YAML validation

Run manually against all files:
```bash
pre-commit run --all-files
```

### Project Structure

```
timeo/
├── __init__.py       # public API
├── decorator.py      # @timeo.track implementation
├── manager.py        # ProgressManager, rich.Progress integration
└── task.py           # TrackedTask dataclass/model
```

## Timing-Based Progress Estimation

### Overview

An opt-in mode (`@timeo.track(learn=True)`) that drives the progress bar using elapsed time against an expected duration gleaned from previous runs of that function. Rather than tracking discrete steps, the bar fills as `elapsed / expected_duration`.

### Opt-In Behavior

- Default behavior is **unchanged** — `@timeo.track` with no arguments works as always (step-based or indeterminate).
- Time-based estimation is activated explicitly: `@timeo.track(learn=True)`.
- On the **first run** (no cached data yet), display an indeterminate progress bar with a "Learning timing..." label so the user knows data is being collected but no estimate is available yet.
- On subsequent runs, use the cached EMA estimate to render a determinate time-driven progress bar.

### Local Timing Cache

- The cache location is user-configurable via the `cache` parameter on `@timeo.track`:
  - `cache="user"` (default) — stores at the platform user cache dir (e.g. `~/Library/Caches/timeo/timings.json` on macOS). Uses `platformdirs` for cross-platform path resolution.
  - `cache="project"` — stores at `.timeo/timings.json` relative to `cwd()` at decoration time.
- The path is resolved once when the decorator is applied (not on each call), so `cwd()` is captured at import/decoration time.
- An invalid `cache=` value raises `ValueError` at decoration time.
- Each entry is keyed by a **hash of the function's bytecode** (`dis` or `inspect` + `hashlib`) rather than its name or module path. This ensures the cache automatically invalidates when the function's implementation changes — a refactored or updated function is treated as a new function with no prior data.
- Cache entry schema:
  ```json
  {
    "<fn_hash>": {
      "name": "my_module.process_files",
      "ema_duration_seconds": 12.4,
      "run_count": 7,
      "last_updated": "2026-04-08T00:00:00Z"
    }
  }
  ```
- `name` is stored for human readability/debugging only — it is never used as a lookup key.

### EMA Strategy

- After each run completes, update the stored estimate using an **Exponential Moving Average**:
  ```
  ema = alpha * actual_duration + (1 - alpha) * previous_ema
  ```
- Suggested default `alpha = 0.2` (weights recent runs moderately; can be tuned).
- On the very first run, `ema` is seeded with the actual duration directly (no prior value to blend with).
- The EMA converges quickly enough that estimates become useful within 3–5 runs.

### Progress Bar Behavior

- The bar advances by `elapsed_time / ema_duration`, updated on a tick interval.
- If the function **overruns** the estimate, the bar stalls at ~99% rather than exceeding 100% or erroring — it completes to 100% only when the function actually returns.
- `rich` custom progress columns will be used to render this time-driven bar alongside any step-based bars in the same live display.

### Function Change Detection

- At call time, hash the function's bytecode (`fn.__code__.co_code` or the full `code` object via `marshal`/`hashlib`).
- If the hash does not match any cached entry, treat it as a brand-new function (show "Learning timing..." and start fresh).
- Old/stale entries for the previous hash are not automatically deleted — they accumulate silently. A future cache cleanup utility can address this.

## Design Decisions

### `total` — Inferred from `Sized` args
`timeo` inspects the arguments passed to a decorated function at call time and looks for any that implement `__len__()`. The first `Sized` argument found is used as `total`. No user input required. If no `Sized` argument is found, the bar is indeterminate.

### `advance()` — `contextvars.ContextVar` (under the hood)
`timeo.advance()` uses a `ContextVar` internally to know which task to update. The decorator pushes the current task onto the `ContextVar` before the function runs and pops it when it returns. This is fully transparent to the user — they only call `timeo.advance()`, no context management required. This also makes concurrent functions safe: threads and async tasks each see their own isolated `ContextVar` value.

### Iteration wrapping — `timeo.iter()`
`timeo.iter(items)` is supported as a convenience wrapper that automatically calls `advance()` on each iteration, eliminating the need for manual `advance()` calls:

```python
@timeo.track
def process_files(files):
    for f in timeo.iter(files):
        handle(f)
```

### Concurrent functions — Stacked bars with completed tasks collapsed
Multiple simultaneously-running tracked functions are each given their own row in the live display. When a function completes, its bar collapses to a single summary line with a checkmark and elapsed time. Only in-progress bars are shown in full:

```
✓ process_files    12.4s
download_data    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━  72% 0:00:04
compress_output  ━━━━━━━━━━                 20% 0:00:31
```

### Display lifecycle — Hybrid (automatic with optional explicit control)
By default, the live display starts automatically on the first decorated function call and tears down when the last tracked function finishes. Teardown is guaranteed via `try/finally` in the decorator so exceptions never leave the terminal in a broken state. A reference counter tracks how many tasks are active; the display is torn down when it reaches zero.

For complex scripts where automatic teardown is insufficient (e.g., conditional branching, multiprocessing), the user can take explicit control with a context manager:

```python
with timeo.live():
    process_files(my_files)
    download_data(my_urls)
# display always tears down cleanly here
```
