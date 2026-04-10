<div align="center">

# ⏱ timeo

**Terminal progress bars for Python functions — just add a decorator.**

[![PyPI](https://img.shields.io/pypi/v/timeo?color=blue&label=pypi)](https://pypi.org/project/timeo/)
[![Python](https://img.shields.io/pypi/pyversions/timeo)](https://pypi.org/project/timeo/)
[![License: MIT](https://img.shields.io/badge/license-MIT-green)](LICENSE)
[![CI](https://github.com/wtewalt/timeo/actions/workflows/ci.yml/badge.svg)](https://github.com/wtewalt/timeo/actions)
[![GitHub](https://img.shields.io/badge/github-wtewalt%2Ftimeo-blue?logo=github)](https://github.com/wtewalt/timeo)

```
✓ process_files   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━  100%  12.4s
  download_data   ━━━━━━━━━━━━━━━━━━━━━━━          72%   0:00:04
  compress_output ━━━━━━                           20%   0:00:31
```

</div>

---

## Why timeo?

Most progress bar libraries ask you to wrap your loops manually and manage the display yourself. `timeo` gets out of the way — decorate a function, iterate normally, done.

```python
# before
for item in items:
    process(item)

# after
@timeo.track
def run(items):
    for item in timeo.iter(items):
        process(item)
```

---

## Installation

```bash
pip install timeo
```

---

## Usage

### Basic progress bar

`@timeo.track` wraps any function with a live progress bar. The total is inferred automatically from the first argument with a `len()`. Use `timeo.iter()` to advance the bar on each iteration — no manual bookkeeping needed.

```python
import timeo

@timeo.track
def process_files(files):
    for f in timeo.iter(files):
        do_work(f)

process_files(my_files)
```

Prefer manual control? Use `timeo.advance()` instead:

```python
@timeo.track
def process_files(files):
    for f in files:
        do_work(f)
        timeo.advance()
```

---

### Multiple concurrent functions

Every decorated function gets its own bar. They render together in a single live display. Finished bars collapse to a compact summary line so the output stays clean.

```python
@timeo.track
def process_files(files):
    for f in timeo.iter(files):
        do_work(f)

@timeo.track
def download_data(urls):
    for url in timeo.iter(urls):
        fetch(url)

process_files(my_files)
download_data(my_urls)
```

```
✓ process_files   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━  100%  12.4s
  download_data   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━   72%  0:00:04
```

Concurrent execution (threads) is fully supported — each bar tracks its own function independently.

---

### Learn mode

Add `learn=True` and `timeo` will remember how long your function takes across runs, building an EMA (exponential moving average) of its runtime. Instead of counting steps, the bar fills over the expected duration.

```python
@timeo.track(learn=True)
def run_pipeline(data):
    heavy_computation(data)
    more_work(data)
```

| Run | Behaviour |
|-----|-----------|
| First | Indeterminate spinner with `run_pipeline (learning...)` label |
| Subsequent | Determinate bar filling over the expected duration |
| After code change | Cache invalidates automatically — learning restarts |

The cache key is a hash of the function's bytecode — not its name — so renaming a function preserves its history, and changing its implementation resets it.

By default timing data is stored in your platform's user cache directory (e.g. `~/Library/Caches/timeo/timings.json` on macOS). Use `cache="project"` to store it in `.timeo/timings.json` relative to the current directory instead — useful for per-project isolation or sharing timings with a team via version control:

```python
@timeo.track(learn=True, cache="project")
def run_pipeline(data):
    ...
```

> **Note:** If using `cache="project"`, add `.timeo/` to your `.gitignore` unless you intentionally want to commit timing data.

| `cache=` | Location | Best for |
|---|---|---|
| `"user"` (default) | `~/.cache/timeo/timings.json` | Personal scripts, cross-project reuse |
| `"project"` | `.timeo/timings.json` | Per-project isolation, shared team timings |

---

### Explicit display control

The live display starts and stops automatically in most cases. For complex scripts with branching logic or long-running setup, use `timeo.live()` to pin the display lifetime explicitly:

```python
with timeo.live():
    process_files(my_files)
    download_data(my_urls)
    # display stays open until the with-block exits
```

---

## CLI

`timeo` ships a command-line tool for inspecting and managing the learn-mode cache.

### View cache contents

```bash
timeo cache info                  # user cache (default)
timeo cache info --cache project  # project cache
```

Output:

```
Cache location: /Users/you/Library/Caches/timeo/timings.json
Entries: 2

╭─────────────────────┬──────────────┬──────┬─────────────────────╮
│ Function            │ EMA Duration │ Runs │ Last Updated        │
├─────────────────────┼──────────────┼──────┼─────────────────────┤
│ module.run_pipeline │       12.40s │    7 │ 2026-04-10 09:21:00 │
│ module.process_data │        3.20s │    3 │ 2026-04-09 14:05:12 │
╰─────────────────────┴──────────────┴──────┴─────────────────────╯
```

### Reset the cache

```bash
timeo cache reset                  # delete entire user cache (default)
timeo cache reset --cache project  # delete entire project cache
```

You will be prompted to confirm. Pass `--yes` to skip the prompt:

```bash
timeo cache reset --yes
```

To remove only entries last updated before a specific date, use `--before`:

```bash
timeo cache reset --before 2025-01-01        # remove entries older than Jan 1 2025
timeo cache reset --before 2025-01-01 --yes  # skip confirmation
```

This leaves newer entries intact — useful for pruning stale data without losing recent timing history.

---

## How it works

| Piece | Role |
|---|---|
| `@timeo.track` | Wraps the function, infers `total` from `Sized` args, manages the task lifecycle |
| `ProgressManager` | Singleton owning the `rich` live display; reference-counted so it tears down only when all tasks finish |
| `TrackedTask` | Dataclass holding per-function progress state |
| `timeo.iter()` | Thin generator wrapper that calls `advance()` on each item |
| `ContextVar` | Ensures `timeo.advance()` always updates the *right* bar, even across threads |

The display is built on [`rich.progress`](https://rich.readthedocs.io/en/stable/progress.html) and [`rich.live`](https://rich.readthedocs.io/en/stable/live.html).

---

<div align="center">
  <sub>Built with <a href="https://github.com/Textualize/rich">rich</a> · MIT License</sub>
</div>
