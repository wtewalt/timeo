"""Tests for timeo/cache.py — timing cache I/O and EMA logic."""

import json
from pathlib import Path
from unittest.mock import patch

import pytest

from timeo.cache import (
    ALPHA,
    DRIFT_THRESHOLD,
    DRIFT_WINDOW,
    TimingEntry,
    get_entry,
    load_cache,
    resolve_cache_path,
    save_cache,
    update_entry,
)


def _patch_cache_path(tmp_path: Path):
    """Context manager that redirects _cache_path() to tmp_path."""
    cache_file = tmp_path / "timings.json"
    return patch("timeo.cache._cache_path", return_value=cache_file)


# ---------------------------------------------------------------------------
# load_cache
# ---------------------------------------------------------------------------


def test_load_cache_returns_empty_on_missing_file(tmp_path: Path) -> None:
    with _patch_cache_path(tmp_path):
        assert load_cache() == {}


def test_load_cache_returns_empty_on_corrupt_file(tmp_path: Path) -> None:
    cache_file = tmp_path / "timings.json"
    cache_file.write_text("not valid json", encoding="utf-8")
    with _patch_cache_path(tmp_path):
        assert load_cache() == {}


def test_load_cache_backward_compat_no_recent_durations(tmp_path: Path) -> None:
    """Cache files written before recent_durations was added should load cleanly."""
    cache_file = tmp_path / "timings.json"
    old_format = {
        "abc123": {
            "name": "my_func",
            "ema_duration_seconds": 5.0,
            "run_count": 3,
            "last_updated": "2024-01-01T00:00:00+00:00",
            # no recent_durations key
        }
    }
    cache_file.write_text(json.dumps(old_format), encoding="utf-8")
    result = load_cache(cache_path=cache_file)
    assert "abc123" in result
    assert result["abc123"].recent_durations == []


# ---------------------------------------------------------------------------
# get_entry
# ---------------------------------------------------------------------------


def test_get_entry_returns_none_when_missing(tmp_path: Path) -> None:
    with _patch_cache_path(tmp_path):
        assert get_entry("nonexistent_hash") is None


# ---------------------------------------------------------------------------
# update_entry — basic behaviour
# ---------------------------------------------------------------------------


def test_update_entry_creates_entry(tmp_path: Path) -> None:
    with _patch_cache_path(tmp_path):
        update_entry("abc123", "my_func", 5.0)
        entry = get_entry("abc123")
    assert entry is not None


def test_update_entry_seeds_ema_on_first_run(tmp_path: Path) -> None:
    with _patch_cache_path(tmp_path):
        update_entry("abc123", "my_func", 5.0)
        entry = get_entry("abc123")
    assert entry is not None
    assert entry.ema_duration_seconds == pytest.approx(5.0)
    assert entry.run_count == 1


def test_update_entry_seeds_recent_durations_on_first_run(tmp_path: Path) -> None:
    with _patch_cache_path(tmp_path):
        update_entry("abc123", "my_func", 5.0)
        entry = get_entry("abc123")
    assert entry is not None
    assert entry.recent_durations == [5.0]


def test_update_entry_increments_run_count(tmp_path: Path) -> None:
    with _patch_cache_path(tmp_path):
        update_entry("abc123", "my_func", 1.0)
        update_entry("abc123", "my_func", 2.0)
        update_entry("abc123", "my_func", 3.0)
        entry = get_entry("abc123")
    assert entry is not None
    assert entry.run_count == 3


def test_update_entry_stores_name(tmp_path: Path) -> None:
    with _patch_cache_path(tmp_path):
        update_entry("abc123", "MyClass.my_method", 2.0)
        entry = get_entry("abc123")
    assert entry is not None
    assert entry.name == "MyClass.my_method"


def test_different_hashes_stored_independently(tmp_path: Path) -> None:
    with _patch_cache_path(tmp_path):
        update_entry("hash_a", "func_a", 3.0)
        update_entry("hash_b", "func_b", 7.0)
        entry_a = get_entry("hash_a")
        entry_b = get_entry("hash_b")
    assert entry_a is not None
    assert entry_b is not None
    assert entry_a.ema_duration_seconds == pytest.approx(3.0)
    assert entry_b.ema_duration_seconds == pytest.approx(7.0)


def test_cache_file_is_valid_json_after_write(tmp_path: Path) -> None:
    cache_file = tmp_path / "timings.json"
    with _patch_cache_path(tmp_path):
        update_entry("abc123", "my_func", 4.0)
    raw = json.loads(cache_file.read_text(encoding="utf-8"))
    assert "abc123" in raw


# ---------------------------------------------------------------------------
# Approach D — decaying alpha
# ---------------------------------------------------------------------------


def test_decaying_alpha_run2_uses_half_weight(tmp_path: Path) -> None:
    """On the second run new_run_count=2 so alpha=max(0.2, 0.5)=0.5."""
    cache_file = tmp_path / "timings.json"
    update_entry("abc123", "my_func", 10.0, cache_path=cache_file)  # seed
    update_entry("abc123", "my_func", 0.0, cache_path=cache_file)  # run 2
    entry = get_entry("abc123", cache_path=cache_file)
    assert entry is not None
    # alpha=0.5 → ema = 0.5*0.0 + 0.5*10.0 = 5.0
    assert entry.ema_duration_seconds == pytest.approx(5.0)


def test_decaying_alpha_run3(tmp_path: Path) -> None:
    """On run 3 alpha=max(0.2, 1/3)≈0.333."""
    cache_file = tmp_path / "timings.json"
    update_entry("h", "f", 10.0, cache_path=cache_file)  # run 1: ema=10
    update_entry(
        "h", "f", 10.0, cache_path=cache_file
    )  # run 2: ema stays 10 (same value)
    update_entry("h", "f", 4.0, cache_path=cache_file)  # run 3: alpha≈0.333
    entry = get_entry("h", cache_path=cache_file)
    assert entry is not None
    # alpha = max(0.2, 1/3) = 1/3
    expected = (1 / 3) * 4.0 + (2 / 3) * 10.0
    assert entry.ema_duration_seconds == pytest.approx(expected, rel=1e-3)


def test_decaying_alpha_floors_at_alpha_after_run5(tmp_path: Path) -> None:
    """After run 5, alpha floors at ALPHA=0.2 and no longer decays."""
    cache_file = tmp_path / "timings.json"
    for _ in range(5):
        update_entry("h", "f", 10.0, cache_path=cache_file)
    # At run 6, new_run_count=6 → 1/6 < 0.2, so floor kicks in.
    update_entry("h", "f", 0.0, cache_path=cache_file)
    entry = get_entry("h", cache_path=cache_file)
    assert entry is not None
    # If floor is working, alpha == ALPHA == 0.2
    # ema before last run was ~10.0 (all previous values were 10.0)
    expected = ALPHA * 0.0 + (1 - ALPHA) * 10.0
    assert entry.ema_duration_seconds == pytest.approx(expected, rel=1e-3)


# ---------------------------------------------------------------------------
# Approach C — drift detection
# ---------------------------------------------------------------------------


def test_drift_detection_no_reset_during_warmup(tmp_path: Path) -> None:
    """Drift is never triggered during the first DRIFT_WINDOW+1 warm-up runs.

    Without this guard, naturally ascending early values (1s, 2s, 3s) would
    produce avg_recent > EMA and incorrectly reset the entry before it has
    had a chance to converge.
    """
    cache_file = tmp_path / "timings.json"
    # Three ascending values — would trigger drift without the warm-up guard.
    update_entry("h", "f", 1.0, cache_path=cache_file)
    update_entry("h", "f", 2.0, cache_path=cache_file)
    update_entry("h", "f", 3.0, cache_path=cache_file)
    entry = get_entry("h", cache_path=cache_file)
    assert entry is not None
    assert entry.run_count == 3  # no spurious reset


def test_drift_detection_resets_on_sustained_change(tmp_path: Path) -> None:
    """DRIFT_WINDOW consecutive runs ~50% above EMA should trigger a reset.

    Drift detection only activates after entry.run_count > DRIFT_WINDOW, so
    the EMA has had a chance to converge before comparisons begin.  After 8
    stable runs at 10s the EMA converges to 10s.  With new_duration=15s the
    avg_recent only exceeds DRIFT_THRESHOLD once all DRIFT_WINDOW slots are
    filled with the new value (the EMA adjusts slowly via alpha=0.2 so it
    still lags by >25% on run DRIFT_WINDOW).
    """
    cache_file = tmp_path / "timings.json"
    # Converge EMA to 10s.
    for _ in range(8):
        update_entry("h", "f", 10.0, cache_path=cache_file)

    entry_before = get_entry("h", cache_path=cache_file)
    assert entry_before is not None
    assert entry_before.ema_duration_seconds == pytest.approx(10.0, rel=0.05)

    # 15s is ~50% above 10s.  Tracing the math:
    #   run N+1: recent=[10,10,15], avg=11.67, ema=10  → dev=0.167 < 0.25, no reset
    #   run N+2: recent=[10,15,15], avg=13.33, ema=11  → dev=0.212 < 0.25, no reset
    #   run N+3: recent=[15,15,15], avg=15,   ema=11.8 → dev=0.271 > 0.25, RESET ✓
    new_duration = 15.0
    for _ in range(DRIFT_WINDOW):
        update_entry("h", "f", new_duration, cache_path=cache_file)

    entry_after = get_entry("h", cache_path=cache_file)
    assert entry_after is not None
    # After a drift reset, run_count should be back to 1.
    assert entry_after.run_count == 1
    assert entry_after.ema_duration_seconds == pytest.approx(new_duration)


def test_drift_detection_no_reset_on_mild_variation(tmp_path: Path) -> None:
    """Mild variation (~20% above EMA) never triggers a drift reset."""
    cache_file = tmp_path / "timings.json"
    for _ in range(8):
        update_entry("h", "f", 10.0, cache_path=cache_file)

    run_count_before = get_entry("h", cache_path=cache_file).run_count  # type: ignore[union-attr]

    # 12s is 20% above 10s — well below DRIFT_THRESHOLD=0.25 once averaged
    # over the window, so drift should never trigger.
    for _ in range(DRIFT_WINDOW + 3):
        update_entry("h", "f", 12.0, cache_path=cache_file)

    entry = get_entry("h", cache_path=cache_file)
    assert entry is not None
    # run_count should have continued incrementing, not reset to 1.
    assert entry.run_count > run_count_before


def test_drift_detection_stores_recent_durations(tmp_path: Path) -> None:
    """recent_durations window should not exceed DRIFT_WINDOW entries."""
    cache_file = tmp_path / "timings.json"
    for i in range(DRIFT_WINDOW + 3):
        update_entry("h", "f", float(i), cache_path=cache_file)
    entry = get_entry("h", cache_path=cache_file)
    assert entry is not None
    assert len(entry.recent_durations) <= DRIFT_WINDOW


# ---------------------------------------------------------------------------
# resolve_cache_path
# ---------------------------------------------------------------------------


def test_resolve_cache_path_user_contains_timeo() -> None:
    path = resolve_cache_path("user")
    assert "timeo" in str(path)
    assert path.name == "timings.json"


def test_resolve_cache_path_project(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    path = resolve_cache_path("project")
    assert path == tmp_path / ".timeo" / "timings.json"


def test_resolve_cache_path_invalid_raises() -> None:
    with pytest.raises(ValueError, match="Invalid cache location"):
        resolve_cache_path("bogus")


# ---------------------------------------------------------------------------
# cache_path parameter threading
# ---------------------------------------------------------------------------


def test_get_entry_uses_supplied_cache_path(tmp_path: Path) -> None:
    cache_file = tmp_path / "custom.json"
    update_entry("abc123", "my_func", 5.0, cache_path=cache_file)
    entry = get_entry("abc123", cache_path=cache_file)
    assert entry is not None
    assert entry.ema_duration_seconds == pytest.approx(5.0)


def test_update_entry_writes_to_supplied_cache_path(tmp_path: Path) -> None:
    cache_file = tmp_path / "sub" / "timings.json"
    update_entry("abc123", "my_func", 3.0, cache_path=cache_file)
    assert cache_file.exists()
    raw = json.loads(cache_file.read_text(encoding="utf-8"))
    assert "abc123" in raw


def test_load_cache_uses_supplied_cache_path(tmp_path: Path) -> None:
    cache_file = tmp_path / "timings.json"
    update_entry("abc123", "my_func", 2.0, cache_path=cache_file)
    result = load_cache(cache_path=cache_file)
    assert "abc123" in result


# ---------------------------------------------------------------------------
# Approach B — depends_on (integration with hashing; full decorator tests
# live in test_hashing.py and test_decorator.py)
# ---------------------------------------------------------------------------


def test_cache_key_differs_with_different_deps(tmp_path: Path) -> None:
    """Two separate cache keys (from different dep hashes) are independent."""
    cache_file = tmp_path / "timings.json"
    update_entry("hash_nodep", "f", 5.0, cache_path=cache_file)
    update_entry("hash_withdep", "f", 99.0, cache_path=cache_file)

    entry_nodep = get_entry("hash_nodep", cache_path=cache_file)
    entry_dep = get_entry("hash_withdep", cache_path=cache_file)

    assert entry_nodep is not None
    assert entry_dep is not None
    assert entry_nodep.ema_duration_seconds != entry_dep.ema_duration_seconds
