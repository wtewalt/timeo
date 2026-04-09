"""Tests for timeo/cache.py — timing cache I/O and EMA logic."""

import json
from pathlib import Path
from unittest.mock import patch

import pytest

from timeo.cache import ALPHA, TimingEntry, get_entry, load_cache, update_entry


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


# ---------------------------------------------------------------------------
# get_entry
# ---------------------------------------------------------------------------


def test_get_entry_returns_none_when_missing(tmp_path: Path) -> None:
    with _patch_cache_path(tmp_path):
        assert get_entry("nonexistent_hash") is None


# ---------------------------------------------------------------------------
# update_entry
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


def test_update_entry_applies_ema(tmp_path: Path) -> None:
    with _patch_cache_path(tmp_path):
        update_entry("abc123", "my_func", 10.0)  # seed: ema = 10.0
        update_entry("abc123", "my_func", 5.0)  # ema = 0.2*5 + 0.8*10 = 9.0
        entry = get_entry("abc123")
    assert entry is not None
    expected = ALPHA * 5.0 + (1 - ALPHA) * 10.0
    assert entry.ema_duration_seconds == pytest.approx(expected)


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
