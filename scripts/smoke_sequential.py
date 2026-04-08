"""
Smoke test 1: sequential decorated functions.

Run with:
    python scripts/smoke_sequential.py
"""

import time

import timeo


@timeo.track
def process_files(files: list[str]) -> None:
    for _ in timeo.iter(files):
        time.sleep(0.05)


@timeo.track
def download_data(urls: list[str]) -> None:
    for _ in timeo.iter(urls):
        time.sleep(0.08)


if __name__ == "__main__":
    process_files([f"file_{i}.txt" for i in range(20)])
    download_data([f"https://example.com/{i}" for i in range(15)])
    print("Done.")
