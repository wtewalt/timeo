"""Tests for learn mode behaviour in timeo/decorator.py."""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from timeo.cache import TimingEntry
from timeo.decorator import track


def _make_entry(ema: float = 5.0, run_count: int = 3) -> TimingEntry:
    return TimingEntry(
        name="my_func",
        ema_duration_seconds=ema,
        run_count=run_count,
        last_updated="2026-01-01T00:00:00+00:00",
    )


# ---------------------------------------------------------------------------
# Helpers to introspect the TrackedTask created inside the wrapper
# ---------------------------------------------------------------------------


def _capture_task(mocker, get_entry_return=None, update_entry_side_effect=None):
    """Patch ProgressManager and cache functions; return captured start_task calls."""
    mock_manager = mocker.patch("timeo.decorator.ProgressManager")
    captured = []

    def fake_start_task(task):
        captured.append(task)

    mock_manager.get.return_value.start_task.side_effect = fake_start_task
    mocker.patch("timeo.decorator.get_entry", return_value=get_entry_return)
    mock_update = mocker.patch("timeo.decorator.update_entry")
    return captured, mock_update


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


def test_learn_mode_first_run_uses_indeterminate(mocker) -> None:
    """On first run (no cache entry), task has ema_duration_seconds=None."""
    captured, _ = _capture_task(mocker, get_entry_return=None)

    @track(learn=True)
    def my_func() -> None:
        pass

    my_func()

    assert len(captured) == 1
    task = captured[0]
    assert task.learn is True
    assert task.ema_duration_seconds is None
    assert "(learning...)" in task.name


def test_learn_mode_first_run_label(mocker) -> None:
    """On first run, the task name includes the learning label."""
    captured, _ = _capture_task(mocker, get_entry_return=None)

    @track(learn=True)
    def pipeline() -> None:
        pass

    pipeline()
    assert captured[0].name == "pipeline (learning...)"


def test_learn_mode_subsequent_run_uses_ema(mocker) -> None:
    """On subsequent run (cache entry present), task has ema_duration_seconds set."""
    entry = _make_entry(ema=8.5)
    captured, _ = _capture_task(mocker, get_entry_return=entry)

    @track(learn=True)
    def my_func() -> None:
        pass

    my_func()

    assert len(captured) == 1
    task = captured[0]
    assert task.learn is True
    assert task.ema_duration_seconds == pytest.approx(8.5)
    assert "(learning...)" not in task.name


def test_learn_mode_updates_cache_after_run(mocker) -> None:
    """update_entry is called with the correct hash and a positive elapsed time."""
    _, mock_update = _capture_task(mocker, get_entry_return=None)
    mocker.patch("timeo.decorator.hash_function", return_value="deadbeef")

    @track(learn=True)
    def my_func() -> None:
        pass

    my_func()

    mock_update.assert_called_once()
    call_args = mock_update.call_args
    assert call_args[0][0] == "deadbeef"  # fn_hash
    assert call_args[0][1] == "my_func"  # qualname
    assert call_args[0][2] >= 0.0  # elapsed


def test_learn_mode_updates_cache_on_exception(mocker) -> None:
    """update_entry is still called even if the wrapped function raises."""
    _, mock_update = _capture_task(mocker, get_entry_return=None)

    @track(learn=True)
    def my_func() -> None:
        raise RuntimeError("oops")

    with pytest.raises(RuntimeError):
        my_func()

    mock_update.assert_called_once()


def test_learn_mode_does_not_affect_standard_track(mocker) -> None:
    """@timeo.track without learn=True never calls update_entry."""
    _, mock_update = _capture_task(mocker, get_entry_return=None)

    @track
    def my_func(items: list) -> None:
        pass

    my_func([1, 2, 3])

    mock_update.assert_not_called()
