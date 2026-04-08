"""
Smoke test 3: explicit display lifecycle via timeo.live().

Verifies that:
- The display stays open after process() returns (while inside the with-block).
- The display tears down cleanly when the with-block exits.

Run with:
    python scripts/smoke_live_context.py
"""

import time

import timeo


@timeo.track
def process(items: list[int]) -> None:
    for _ in timeo.iter(items):
        time.sleep(0.05)


if __name__ == "__main__":
    with timeo.live():
        process(list(range(20)))
        # Display stays open here even though process() has returned.
        print("Function done — display still live for 1s...")
        time.sleep(1)
    # Display closes cleanly here.
    print("Done.")
