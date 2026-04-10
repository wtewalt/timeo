"""Tests for timeo/cli.py — cache info and reset commands."""

from datetime import datetime, timezone
from pathlib import Path

import pytest
from click.testing import CliRunner

from timeo.cache import TimingEntry, save_cache, update_entry
from timeo.cli import cli


@pytest.fixture()
def runner() -> CliRunner:
    return CliRunner()


@pytest.fixture()
def populated_cache(tmp_path: Path, monkeypatch):
    """Patch _cache_path to use tmp_path and seed two entries."""
    cache_file = tmp_path / "timings.json"
    monkeypatch.setattr("timeo.cli.resolve_cache_path", lambda loc: cache_file)
    update_entry("hash_a", "module.func_a", 5.0, cache_path=cache_file)
    update_entry("hash_b", "module.func_b", 12.3, cache_path=cache_file)
    return cache_file


@pytest.fixture()
def empty_cache_path(tmp_path: Path, monkeypatch):
    """Patch resolve_cache_path to a non-existent file in tmp_path."""
    cache_file = tmp_path / "timings.json"
    monkeypatch.setattr("timeo.cli.resolve_cache_path", lambda loc: cache_file)
    return cache_file


# ---------------------------------------------------------------------------
# cache info
# ---------------------------------------------------------------------------


def test_cache_info_shows_location(runner: CliRunner, populated_cache: Path) -> None:
    result = runner.invoke(cli, ["cache", "info", "--cache", "user"])
    assert result.exit_code == 0
    assert "Cache location:" in result.output


def test_cache_info_shows_entries(runner: CliRunner, populated_cache: Path) -> None:
    result = runner.invoke(cli, ["cache", "info"])
    assert result.exit_code == 0
    assert "func_a" in result.output
    assert "func_b" in result.output


def test_cache_info_shows_entry_count(runner: CliRunner, populated_cache: Path) -> None:
    result = runner.invoke(cli, ["cache", "info"])
    assert result.exit_code == 0
    assert "2" in result.output


def test_cache_info_missing_file(runner: CliRunner, empty_cache_path: Path) -> None:
    result = runner.invoke(cli, ["cache", "info"])
    assert result.exit_code == 0
    assert "does not exist" in result.output


def test_cache_info_project_flag(runner: CliRunner, populated_cache: Path) -> None:
    result = runner.invoke(cli, ["cache", "info", "--cache", "project"])
    assert result.exit_code == 0


def test_cache_info_invalid_flag(runner: CliRunner) -> None:
    result = runner.invoke(cli, ["cache", "info", "--cache", "bogus"])
    assert result.exit_code != 0


# ---------------------------------------------------------------------------
# cache reset
# ---------------------------------------------------------------------------


def test_cache_reset_deletes_file(runner: CliRunner, populated_cache: Path) -> None:
    assert populated_cache.exists()
    result = runner.invoke(cli, ["cache", "reset", "--yes"])
    assert result.exit_code == 0
    assert not populated_cache.exists()


def test_cache_reset_confirms_deletion(
    runner: CliRunner, populated_cache: Path
) -> None:
    result = runner.invoke(cli, ["cache", "reset", "--yes"])
    assert "✓" in result.output or "reset" in result.output.lower()


def test_cache_reset_missing_file(runner: CliRunner, empty_cache_path: Path) -> None:
    result = runner.invoke(cli, ["cache", "reset", "--yes"])
    assert result.exit_code == 0
    assert "does not exist" in result.output


def test_cache_reset_prompts_without_yes_flag(
    runner: CliRunner, populated_cache: Path
) -> None:
    # Decline the prompt — file should not be deleted.
    result = runner.invoke(cli, ["cache", "reset"], input="n\n")
    assert result.exit_code != 0
    assert populated_cache.exists()


# ---------------------------------------------------------------------------
# cache reset --before
# ---------------------------------------------------------------------------


@pytest.fixture()
def dated_cache(tmp_path: Path, monkeypatch):
    """Cache with two entries at known timestamps."""
    cache_file = tmp_path / "timings.json"
    monkeypatch.setattr("timeo.cli.resolve_cache_path", lambda loc: cache_file)
    monkeypatch.setattr("timeo.cache.resolve_cache_path", lambda loc: cache_file)

    old_entry = TimingEntry(
        name="module.old_func",
        ema_duration_seconds=3.0,
        run_count=2,
        last_updated="2024-01-01T00:00:00+00:00",
    )
    new_entry = TimingEntry(
        name="module.new_func",
        ema_duration_seconds=5.0,
        run_count=4,
        last_updated="2026-01-01T00:00:00+00:00",
    )
    save_cache({"old_hash": old_entry, "new_hash": new_entry}, cache_path=cache_file)
    return cache_file


def test_before_removes_old_entries(runner: CliRunner, dated_cache: Path) -> None:
    result = runner.invoke(cli, ["cache", "reset", "--before", "2025-01-01", "--yes"])
    assert result.exit_code == 0
    assert "Removed" in result.output
    assert "1" in result.output


def test_before_preserves_new_entries(runner: CliRunner, dated_cache: Path) -> None:
    runner.invoke(cli, ["cache", "reset", "--before", "2025-01-01", "--yes"])
    # Cache file should still exist with the newer entry intact.
    assert dated_cache.exists()
    from timeo.cache import load_cache

    remaining = load_cache(cache_path=dated_cache)
    assert "new_hash" in remaining
    assert "old_hash" not in remaining


def test_before_no_matching_entries(runner: CliRunner, dated_cache: Path) -> None:
    # Date before all entries — nothing should be removed.
    result = runner.invoke(cli, ["cache", "reset", "--before", "2020-01-01", "--yes"])
    assert result.exit_code == 0
    assert "No entries found" in result.output


def test_before_invalid_date_format(runner: CliRunner, populated_cache: Path) -> None:
    result = runner.invoke(cli, ["cache", "reset", "--before", "not-a-date", "--yes"])
    assert result.exit_code != 0
    assert "Invalid date" in result.output


def test_before_prompts_with_date_context(runner: CliRunner, dated_cache: Path) -> None:
    # Provide "n" to decline — should show date in prompt.
    result = runner.invoke(
        cli, ["cache", "reset", "--before", "2025-01-01"], input="n\n"
    )
    assert "2025-01-01" in result.output
    assert result.exit_code != 0
