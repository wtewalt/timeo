"""
cache — local timing cache for learn-mode EMA estimates.

Cache keys are function bytecode hashes — not names — so entries automatically
invalidate when a function's implementation changes.

Two storage locations are supported:
- "user"    (default) ~/.cache/timeo/timings.json  — persists across projects
- "project"           .timeo/timings.json           — scoped to the current project

Estimate quality improvements
------------------------------
D — Decaying alpha:
    Early runs use a higher alpha so the estimate converges quickly from a cold
    start.  alpha = max(ALPHA, 1 / new_run_count), which gives a true running
    average for the first few runs before settling at the steady-state ALPHA.

C — Drift detection:
    The last DRIFT_WINDOW actual durations are stored alongside the EMA.  If
    their average deviates from the stored EMA by more than DRIFT_THRESHOLD, the
    entry is reset as if it were a brand-new function.  This transparently
    handles cases where a called function's implementation changed without the
    decorated function's own bytecode changing.

B — Explicit dependency hashing (see timeo/hashing.py and timeo/decorator.py):
    Users may declare depends_on=[nested_fn, ...] on @timeo.track so that
    changes to any listed dependency invalidate the cache key automatically.
"""

from __future__ import annotations

import json
import os
import tempfile
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from platformdirs import user_cache_dir

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

ALPHA: float = 0.2  # steady-state EMA smoothing factor (floor for decaying alpha)
DRIFT_WINDOW: int = 3  # number of recent runs used for drift detection
DRIFT_THRESHOLD: float = 0.25  # fractional deviation that triggers an EMA reset
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
    recent_durations: list[float] = field(
        default_factory=list
    )  # last DRIFT_WINDOW runs


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
        # Gracefully handle cache files written before recent_durations was added.
        recent_durations=[float(d) for d in data.get("recent_durations", [])],
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
    """Update (or create) the cache entry for fn_hash.

    Implements two accuracy improvements over a plain fixed-alpha EMA:

    * **Decaying alpha** (approach D): uses ``alpha = max(ALPHA, 1/new_run_count)``
      so early runs converge quickly to a true running average before the
      steady-state ALPHA takes over around run 5.

    * **Drift detection** (approach C): if the last ``DRIFT_WINDOW`` actual
      durations collectively deviate from the stored EMA by more than
      ``DRIFT_THRESHOLD``, the entry is reset as if the function were new.
      This transparently handles runtime changes caused by modifications to
      called functions whose own bytecode hash is not part of this entry's key.
    """
    cache = load_cache(cache_path)
    entry = cache.get(fn_hash)

    now = datetime.now(timezone.utc).isoformat()

    if entry is None:
        # First ever run — seed the EMA directly from the actual duration.
        new_entry = TimingEntry(
            name=name,
            ema_duration_seconds=actual_duration,
            run_count=1,
            last_updated=now,
            recent_durations=[actual_duration],
        )
    else:
        # Append current run to the sliding window (keep at most DRIFT_WINDOW).
        recent = (entry.recent_durations + [actual_duration])[-DRIFT_WINDOW:]

        # --- Approach C: drift detection ---
        # Only check once we have a full window of observations.
        if len(recent) >= DRIFT_WINDOW and entry.ema_duration_seconds > 0:
            avg_recent = sum(recent) / len(recent)
            deviation = (
                abs(avg_recent - entry.ema_duration_seconds)
                / entry.ema_duration_seconds
            )
            if deviation > DRIFT_THRESHOLD:
                # Sustained divergence detected — reset as if this is run 1.
                new_entry = TimingEntry(
                    name=name,
                    ema_duration_seconds=actual_duration,
                    run_count=1,
                    last_updated=now,
                    recent_durations=[actual_duration],
                )
                cache[fn_hash] = new_entry
                save_cache(cache, cache_path)
                return

        # --- Approach D: decaying alpha ---
        # alpha starts high (converges fast) and floors at ALPHA (~run 5).
        new_run_count = entry.run_count + 1
        alpha = max(ALPHA, 1.0 / new_run_count)
        new_ema = alpha * actual_duration + (1 - alpha) * entry.ema_duration_seconds

        new_entry = TimingEntry(
            name=name,
            ema_duration_seconds=new_ema,
            run_count=new_run_count,
            last_updated=now,
            recent_durations=recent,
        )

    cache[fn_hash] = new_entry
    save_cache(cache, cache_path)
