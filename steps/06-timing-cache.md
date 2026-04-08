# Step 6: Timing Cache

## Goal
Implement the local timing cache infrastructure — reading, writing, and keying entries by function bytecode hash. This is the foundation for the `learn=True` opt-in mode, implemented in the next step.

## Tasks

### 1. Add `platformdirs` dependency
Ensure `platformdirs` is in `pyproject.toml` dependencies (added in Step 1). Run `uv sync` to confirm it installs correctly.

### 2. Create `timeo/cache.py`
This module is responsible for all cache I/O. It should have no knowledge of `rich` or the progress display.

#### 2a. Cache path resolution
```python
from platformdirs import user_cache_dir
from pathlib import Path

def _cache_path() -> Path:
    return Path(user_cache_dir("timeo")) / "timings.json"
```

#### 2b. Cache entry schema
Define a `TimingEntry` typed dict or dataclass:

```python
@dataclass
class TimingEntry:
    name: str                    # human-readable, for debugging only
    ema_duration_seconds: float  # current EMA estimate
    run_count: int               # total number of completed runs
    last_updated: str            # ISO 8601 timestamp string
```

#### 2c. `load_cache() -> dict[str, TimingEntry]`
Read and parse `timings.json`. Return an empty dict if the file does not exist or is malformed (never raise on a missing/corrupt cache).

#### 2d. `save_cache(cache: dict[str, TimingEntry]) -> None`
Serialize and write the cache to disk. Create the parent directory if it does not exist.

#### 2e. `get_entry(fn_hash: str) -> TimingEntry | None`
Load the cache and return the entry for `fn_hash`, or `None` if not present.

#### 2f. `update_entry(fn_hash: str, name: str, actual_duration: float) -> None`
Load the cache, update (or create) the entry for `fn_hash` using the EMA formula, then save.

EMA update logic:
```python
ALPHA = 0.2

if entry is None:
    # first run — seed directly
    new_ema = actual_duration
    run_count = 1
else:
    new_ema = ALPHA * actual_duration + (1 - ALPHA) * entry.ema_duration_seconds
    run_count = entry.run_count + 1
```

### 3. Create `timeo/hashing.py`
This module computes a stable hash of a function's bytecode for use as a cache key.

```python
import hashlib
import marshal

def hash_function(fn) -> str:
    """Return a hex digest of the function's bytecode."""
    code_bytes = marshal.dumps(fn.__code__)
    return hashlib.sha256(code_bytes).hexdigest()
```

Use `marshal.dumps(fn.__code__)` to serialize the full code object (includes constants, variable names, and nested code objects — not just `co_code`). This ensures the hash changes if the function body, its constants, or any nested functions change.

## Notes
- The cache file should be valid JSON at all times. Use atomic writes if possible (write to a temp file, then rename) to avoid corruption on crash.
- `last_updated` should be stored as an ISO 8601 UTC string: `datetime.utcnow().isoformat() + "Z"`.
- `ALPHA = 0.2` can be a module-level constant in `cache.py`.

## Acceptance Criteria
- `from timeo.cache import get_entry, update_entry` works without errors.
- `from timeo.hashing import hash_function` works without errors.
- Calling `update_entry` multiple times for the same hash correctly applies the EMA formula.
- The first call to `update_entry` seeds the EMA with the raw duration (run_count = 1).
- `get_entry` returns `None` for an unknown hash.
- The cache file is created at the correct platform-specific path.
- Cache load gracefully returns `{}` if the file is missing or corrupt.
- mypy passes with no errors on both files.
