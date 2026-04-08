# timeo

Terminal progress bars for Python functions, powered by decorators and [`rich`](https://github.com/Textualize/rich).

Decorate any function with `@timeo.track` and get a live progress bar in your terminal automatically — no manual wiring required.

---

## Installation

```bash
pip install timeo
```

---

## Usage

### Basic — step-based progress

Apply `@timeo.track` to any function. `timeo` will infer the total number of steps from the first argument that has a `len()`. Use `timeo.iter()` inside the function to advance the bar automatically on each iteration:

```python
import timeo

@timeo.track
def process_files(files):
    for f in timeo.iter(files):
        do_work(f)

process_files(my_files)
```

Or advance manually with `timeo.advance()` if you need finer control:

```python
@timeo.track
def process_files(files):
    for f in files:
        do_work(f)
        timeo.advance()
```

Terminal output while running:

```
process_files  ━━━━━━━━━━━━━━━━━━━━━━━━  45% 0:00:12
```

---

### Multiple functions

Multiple decorated functions each get their own bar. Completed bars collapse to a summary line:

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
✓ process_files   12.4s
download_data   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━  72% 0:00:04
```

---

### Learn mode — time-based progress

Use `learn=True` to have `timeo` learn how long a function typically takes and use that to drive the progress bar by time instead of steps:

```python
@timeo.track(learn=True)
def run_pipeline(data):
    heavy_computation(data)
    more_work(data)

run_pipeline(my_data)
```

- **First run:** shows an indeterminate bar labelled `run_pipeline (learning...)` while timing data is collected.
- **Subsequent runs:** shows a determinate bar that fills over the expected duration based on an exponential moving average (EMA) of previous runtimes.
- Timing data is stored locally at `~/.cache/timeo/timings.json`.
- If the function's implementation changes, the cache automatically invalidates and learning restarts.

---

### Explicit display control

By default the live display starts and stops automatically. For complex scripts, use `timeo.live()` to take explicit control:

```python
with timeo.live():
    process_files(my_files)
    download_data(my_urls)
# display always tears down cleanly here
```

---

## How it works

- `@timeo.track` wraps the decorated function and registers it with a central `ProgressManager`.
- `total` is inferred from the first `Sized` argument passed to the function (i.e. anything with `len()`). If none is found, an indeterminate spinner is shown.
- `timeo.iter()` wraps any iterable and calls `timeo.advance()` on each iteration automatically.
- The live display is backed by `rich.progress` and `rich.live`, rendering all active bars together in a single unified display.
- Concurrent functions (e.g. threads) are fully supported — each gets its own bar and the underlying `ContextVar` ensures `timeo.advance()` always updates the correct task.

---

## Contributing

```bash
# Enter the nix development shell first
nix develop

# Install dependencies
uv sync

# Install pre-commit hooks (one-time)
pre-commit install

# Run tests
pytest

# Run all pre-commit checks
pre-commit run --all-files
```

All commits must follow [Conventional Commits](https://www.conventionalcommits.org/). See [`CONVENTIONS.md`](CONVENTIONS.md) for full contribution guidelines.
