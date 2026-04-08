# Step 5: Public API

## Goal
Wire up `timeo/__init__.py` to expose the complete public-facing API and verify the package works end-to-end with a manual smoke test.

## Tasks

### 1. Update `timeo/__init__.py`
Export all user-facing symbols:

```python
"""
timeo — terminal progress bars via decorators.
"""

from timeo.decorator import advance, iter, track
from timeo.manager import ProgressManager as _ProgressManager

def live():
    """Context manager for explicit display lifecycle control."""
    return _ProgressManager.get().live()

__all__ = ["track", "advance", "iter", "live"]
```

### 2. Write a smoke test script
Create a temporary script at `scripts/smoke_test.py` (not part of the package, just for manual verification) that exercises the full basic API:

```python
import time
import timeo

@timeo.track
def process_files(files):
    for f in timeo.iter(files):
        time.sleep(0.05)

@timeo.track
def download_data(urls):
    for url in timeo.iter(urls):
        time.sleep(0.08)

process_files(list(range(20)))
download_data(list(range(15)))
```

Running this script should display live progress bars in the terminal and tear down cleanly on completion.

### 3. Verify concurrent display
Add a second smoke test that runs two decorated functions concurrently using `threading.Thread` to verify that:
- Both bars appear simultaneously in the live display.
- Each bar advances independently.
- Completed tasks collapse to the checkmark + elapsed summary.
- The display tears down when both threads finish.

```python
import threading
import time
import timeo

@timeo.track
def task_a(items):
    for _ in timeo.iter(items):
        time.sleep(0.06)

@timeo.track
def task_b(items):
    for _ in timeo.iter(items):
        time.sleep(0.04)

t1 = threading.Thread(target=task_a, args=(list(range(20)),))
t2 = threading.Thread(target=task_b, args=(list(range(25)),))

t1.start()
t2.start()
t1.join()
t2.join()
```

### 4. Verify `timeo.live()` context manager
Add a smoke test for the explicit lifecycle:

```python
import time
import timeo

@timeo.track
def process(items):
    for _ in timeo.iter(items):
        time.sleep(0.05)

with timeo.live():
    process(list(range(20)))
    # display stays open here even after process() returns
    time.sleep(1)
# display closes cleanly
```

## Acceptance Criteria
- `import timeo` exposes `track`, `advance`, `iter`, and `live`.
- Sequential smoke test runs cleanly with visible progress bars.
- Concurrent smoke test shows both bars simultaneously and collapses completed ones.
- `timeo.live()` context manager keeps the display alive past function completion.
- `pre-commit run --all-files` passes with no errors.
