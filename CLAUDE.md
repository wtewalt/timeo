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

## Open Questions / Decisions to Make

- **How is `total` determined?** — Does the user pass it as a decorator argument (`@timeo.track(total=100)`)? Is it inferred if the function receives a `Sized` iterable?
- **How does `advance()` work?** — Global function that advances the currently-executing tracked task? Context-var based?
- **Automatic iteration wrapping** — Should `timeo` offer a way to auto-wrap a `for` loop (e.g., `for item in timeo.iter(items)`) to auto-advance without manual `advance()` calls?
- **Concurrent functions** — How are two simultaneously-running tracked functions handled? (likely fine with `rich`'s multi-task support)
- **Display lifecycle** — When does the live display start and stop? On first decorated function call? Via a context manager?
