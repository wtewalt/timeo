"""
Smoke test 2: concurrent decorated functions running on separate threads.

Verifies that:
- Both bars appear simultaneously in the live display.
- Each bar advances independently (ContextVar isolation).
- Completed tasks collapse to the checkmark + elapsed summary.
- The display tears down cleanly when both threads finish.

Run with:
    python scripts/smoke_concurrent.py
"""

import threading
import time

import timeo


@timeo.track
def task_a(items: list[int]) -> None:
    for _ in timeo.iter(items):
        time.sleep(0.06)


@timeo.track
def task_b(items: list[int]) -> None:
    for _ in timeo.iter(items):
        time.sleep(0.04)


if __name__ == "__main__":
    t1 = threading.Thread(target=task_a, args=(list(range(20)),))
    t2 = threading.Thread(target=task_b, args=(list(range(25)),))

    t1.start()
    t2.start()
    t1.join()
    t2.join()

    print("Done.")
