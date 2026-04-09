"""
Smoke test: learn mode (@timeo.track(learn=True)).

First run:  indeterminate bar labelled "run_pipeline (learning...)"
Second run: determinate time-driven bar filling over the EMA estimate

Run twice back-to-back to observe the behaviour change:
    python scripts/smoke_learn_mode.py
    python scripts/smoke_learn_mode.py
"""

import time

import timeo


@timeo.track(learn=True)
def run_pipeline(data: list[int]) -> None:
    for _ in data:
        time.sleep(0.05)


if __name__ == "__main__":
    run_pipeline(list(range(20)))
    print("Done. Run again to see the time-driven bar.")
