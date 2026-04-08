"""
cache — local timing cache for learn-mode EMA estimates.

Stores per-function timing data at ~/.cache/timeo/timings.json (platform-aware).
Cache keys are function bytecode hashes — not names — so entries automatically
invalidate when a function's implementation changes.
"""

from __future__ import annotations

import json
import os
import tempfile
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from platformdirs import user_cache_dir

ALPHA: float = 0.2


# ---------------------------------------------------------------------------
# Schema
# ---------------------------------------------------------------------------


@dataclass
class TimingEntry:
    name: str  # human-readable label, for debugging only
    ema_duration_seconds: float  # current EMA estimate in seconds
    run_count: int  # total number of completed runs recorded
    last_updated: str  # ISO 8601 UTC timestamp


# ---------------------------------------------------------------------------
# Path resolution
# ---------------------------------------------------------------------------


def _cache_path() -> Path:
    return Path(user_cache_dir("timeo")) / "timings.json"


# ---------------------------------------------------------------------------
# Serialisation helpers
# ---------------------------------------------------------------------------


def _entry_to_dict(entry: TimingEntry) -> dict[str, Any]:
    return asdict(entry)


def _entry_from_dict(data: dict[str, Any]) -> TimingEntry:
    return TimingEntry(
        name=data["name"],
        ema_duration_seconds=float(data["ema_duration_seconds"]),
        run_count=int(data["run_count"]),
        last_updated=data["last_updated"],
    )


# ---------------------------------------------------------------------------
# I/O
# ---------------------------------------------------------------------------


def load_cache() -> dict[str, TimingEntry]:
    """Load the cache from disk. Returns {} on missing or corrupt file."""
    path = _cache_path()
    if not path.exists():
        return {}
    try:
        raw: dict[str, Any] = json.loads(path.read_text(encoding="utf-8"))
        return {k: _entry_from_dict(v) for k, v in raw.items()}
    except Exception:
        return {}


def save_cache(cache: dict[str, TimingEntry]) -> None:
    """Write the cache to disk atomically (write-then-rename)."""
    path = _cache_path()
    path.parent.mkdir(parents=True, exist_ok=True)

    data = {k: _entry_to_dict(v) for k, v in cache.items()}
    serialised = json.dumps(data, indent=2)

    # Atomic write: write to a temp file in the same directory, then rename.
    fd, tmp_path = tempfile.mkstemp(dir=path.parent, suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(serialised)
        os.replace(tmp_path, path)
    except Exception:
        # Clean up the temp file on failure; do not corrupt the existing cache.
        try:
            os.unlink(tmp_path)
        except OSError:
            pass
        raise


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def get_entry(fn_hash: str) -> TimingEntry | None:
    """Return the cache entry for fn_hash, or None if not found."""
    return load_cache().get(fn_hash)


def update_entry(fn_hash: str, name: str, actual_duration: float) -> None:
    """Update (or create) the cache entry for fn_hash using the EMA formula."""
    cache = load_cache()
    entry = cache.get(fn_hash)

    now = datetime.now(timezone.utc).isoformat()

    if entry is None:
        # First run — seed the EMA directly with the actual duration.
        new_entry = TimingEntry(
            name=name,
            ema_duration_seconds=actual_duration,
            run_count=1,
            last_updated=now,
        )
    else:
        new_ema = ALPHA * actual_duration + (1 - ALPHA) * entry.ema_duration_seconds
        new_entry = TimingEntry(
            name=name,
            ema_duration_seconds=new_ema,
            run_count=entry.run_count + 1,
            last_updated=now,
        )

    cache[fn_hash] = new_entry
    save_cache(cache)
