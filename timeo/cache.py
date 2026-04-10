"""
cache — local timing cache for learn-mode EMA estimates.

Cache keys are function bytecode hashes — not names — so entries automatically
invalidate when a function's implementation changes.

Two storage locations are supported:
- "user"    (default) ~/.cache/timeo/timings.json  — persists across projects
- "project"           .timeo/timings.json           — scoped to the current project
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
_VALID_LOCATIONS = ("user", "project")


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


def resolve_cache_path(location: str = "user") -> Path:
    """Return the cache file path for the given location.

    Args:
        location: ``"user"`` (default) stores in the platform user cache
                  directory. ``"project"`` stores in ``.timeo/timings.json``
                  relative to the current working directory.

    Raises:
        ValueError: If *location* is not ``"user"`` or ``"project"``.
    """
    if location == "user":
        return Path(user_cache_dir("timeo")) / "timings.json"
    if location == "project":
        return Path.cwd() / ".timeo" / "timings.json"
    raise ValueError(
        f"Invalid cache location {location!r}. Choose 'user' or 'project'."
    )


# kept for internal/test use
def _cache_path(location: str = "user") -> Path:
    return resolve_cache_path(location)


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


def load_cache(cache_path: Path | None = None) -> dict[str, TimingEntry]:
    """Load the cache from disk. Returns {} on missing or corrupt file."""
    path = cache_path if cache_path is not None else _cache_path()
    if not path.exists():
        return {}
    try:
        raw: dict[str, Any] = json.loads(path.read_text(encoding="utf-8"))
        return {k: _entry_from_dict(v) for k, v in raw.items()}
    except Exception:
        return {}


def save_cache(cache: dict[str, TimingEntry], cache_path: Path | None = None) -> None:
    """Write the cache to disk atomically (write-then-rename)."""
    path = cache_path if cache_path is not None else _cache_path()
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
        try:
            os.unlink(tmp_path)
        except OSError:
            pass
        raise


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def get_entry(fn_hash: str, cache_path: Path | None = None) -> TimingEntry | None:
    """Return the cache entry for fn_hash, or None if not found."""
    return load_cache(cache_path).get(fn_hash)


def prune_entries_before(
    cutoff: datetime, cache_path: Path | None = None
) -> tuple[int, int]:
    """Remove all entries last updated before *cutoff*.

    Returns a ``(removed, remaining)`` tuple.
    """
    cache = load_cache(cache_path)
    before: dict[str, TimingEntry] = {}
    after: dict[str, TimingEntry] = {}

    for fn_hash, entry in cache.items():
        try:
            updated = datetime.fromisoformat(entry.last_updated)
            # Ensure both datetimes are comparable (make cutoff timezone-aware
            # if the stored timestamp is, and vice-versa).
            if updated.tzinfo is None and cutoff.tzinfo is not None:
                updated = updated.replace(tzinfo=timezone.utc)
            elif updated.tzinfo is not None and cutoff.tzinfo is None:
                cutoff = cutoff.replace(tzinfo=timezone.utc)
        except ValueError:
            # Unparseable timestamp — treat as old and remove it.
            before[fn_hash] = entry
            continue

        if updated < cutoff:
            before[fn_hash] = entry
        else:
            after[fn_hash] = entry

    if before:
        save_cache(after, cache_path)

    return len(before), len(after)


def update_entry(
    fn_hash: str,
    name: str,
    actual_duration: float,
    cache_path: Path | None = None,
) -> None:
    """Update (or create) the cache entry for fn_hash using the EMA formula."""
    cache = load_cache(cache_path)
    entry = cache.get(fn_hash)

    now = datetime.now(timezone.utc).isoformat()

    if entry is None:
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
    save_cache(cache, cache_path)
