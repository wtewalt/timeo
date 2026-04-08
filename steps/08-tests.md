# Step 8: Tests

## Goal
Write an automated test suite covering the core logic of `timeo`. Tests should not depend on terminal rendering — mock or suppress `rich` output where needed.

## Tasks

### 1. Set up the test infrastructure
- Add `pytest` and `pytest-mock` as dev dependencies in `pyproject.toml` under `[dependency-groups]` (or `[project.optional-dependencies]`).
- Run `uv sync` to install them.
- Create a `tests/` directory at the repo root with an empty `__init__.py`.

### 2. Test `timeo/task.py` — `tests/test_task.py`

| Test | Description |
|---|---|
| `test_advance_increments_completed` | `advance()` correctly increments `completed` by the given amount. |
| `test_advance_does_not_exceed_total` | `advance()` does not push `completed` past `total` when `total` is set. |
| `test_fraction_complete_none_when_no_total` | `fraction_complete` returns `None` when `total` is `None`. |
| `test_fraction_complete_correct` | `fraction_complete` returns the correct float when `total` is set. |
| `test_fraction_complete_at_completion` | `fraction_complete` returns `1.0` when `completed == total`. |

### 3. Test `timeo/hashing.py` — `tests/test_hashing.py`

| Test | Description |
|---|---|
| `test_same_function_same_hash` | Hashing the same function twice returns the same value. |
| `test_different_functions_different_hash` | Two different functions produce different hashes. |
| `test_modified_function_different_hash` | Dynamically compiling two code objects with different bodies produces different hashes. |

### 4. Test `timeo/cache.py` — `tests/test_cache.py`

Use `tmp_path` (pytest fixture) to redirect the cache to a temporary directory — patch `timeo.cache._cache_path` to return a path inside `tmp_path`.

| Test | Description |
|---|---|
| `test_get_entry_returns_none_when_missing` | `get_entry` returns `None` for an unknown hash. |
| `test_update_entry_creates_entry` | `update_entry` creates a new entry on first call. |
| `test_update_entry_seeds_ema_on_first_run` | EMA equals `actual_duration` on the first update. |
| `test_update_entry_applies_ema` | Subsequent updates apply the EMA formula correctly (`alpha=0.2`). |
| `test_update_entry_increments_run_count` | `run_count` increments with each `update_entry` call. |
| `test_load_cache_returns_empty_on_missing_file` | `load_cache` returns `{}` when the cache file does not exist. |
| `test_load_cache_returns_empty_on_corrupt_file` | `load_cache` returns `{}` when the cache file contains invalid JSON. |

### 5. Test `timeo/decorator.py` — `tests/test_decorator.py`

Mock `ProgressManager` to suppress all `rich` rendering during tests.

| Test | Description |
|---|---|
| `test_track_calls_wrapped_function` | The decorated function is called and returns its value normally. |
| `test_track_infers_total_from_sized_arg` | `_infer_total` returns `len()` of the first `Sized` argument. |
| `test_track_infers_none_when_no_sized_arg` | `_infer_total` returns `None` when no `Sized` argument is present. |
| `test_advance_updates_current_task` | `timeo.advance()` calls `ProgressManager.advance_task` with the active task. |
| `test_advance_noop_outside_tracked_function` | `timeo.advance()` does not raise when called outside a decorated function. |
| `test_iter_auto_advances` | `timeo.iter()` calls `advance()` once per item yielded. |
| `test_context_var_reset_on_exception` | `_current_task` is reset to `None` even when the wrapped function raises. |
| `test_track_parameterized_form` | `@timeo.track(learn=False)` works identically to `@timeo.track`. |

### 6. Test learn mode — `tests/test_learn_mode.py`

Patch `timeo.cache` functions and `ProgressManager` to avoid I/O and rendering.

| Test | Description |
|---|---|
| `test_learn_mode_first_run_uses_indeterminate` | On first run (no cache entry), task is created with `ema_duration_seconds=None`. |
| `test_learn_mode_subsequent_run_uses_ema` | On subsequent run (cache entry present), task is created with `ema_duration_seconds` set. |
| `test_learn_mode_updates_cache_after_run` | `update_entry` is called with the correct hash and elapsed time after the function returns. |
| `test_learn_mode_updates_cache_on_exception` | `update_entry` is still called even if the wrapped function raises. |

## Notes
- All tests must pass with `pytest` from the repo root.
- No test should write to the real `~/.cache/timeo/` directory.
- No test should render anything to the terminal — mock `ProgressManager` at the boundary.

## Acceptance Criteria
- `pytest` runs and all tests pass.
- `pytest --tb=short -q` produces no failures or errors.
- `pre-commit run --all-files` passes (ruff, mypy, formatting).
- Coverage of `task.py`, `hashing.py`, `cache.py`, and `decorator.py` is meaningful (aim for >80%).
