"""Tests for timeo/cli.py — cache info and reset commands."""

from pathlib import Path

import pytest
from click.testing import CliRunner

from timeo.cache import update_entry
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
