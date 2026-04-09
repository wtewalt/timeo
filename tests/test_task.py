"""Tests for timeo/task.py — TrackedTask model."""

import pytest

from timeo.task import TrackedTask


def test_advance_increments_completed() -> None:
    task = TrackedTask(name="t", total=10)
    task.advance(3)
    assert task.completed == 3


def test_advance_default_amount_is_one() -> None:
    task = TrackedTask(name="t", total=10)
    task.advance()
    assert task.completed == 1


def test_advance_does_not_exceed_total() -> None:
    task = TrackedTask(name="t", total=5)
    task.advance(10)
    assert task.completed == 5


def test_advance_no_total_is_unbounded() -> None:
    task = TrackedTask(name="t", total=None)
    task.advance(100)
    assert task.completed == 100


def test_fraction_complete_none_when_no_total() -> None:
    task = TrackedTask(name="t", total=None)
    assert task.fraction_complete is None


def test_fraction_complete_correct() -> None:
    task = TrackedTask(name="t", total=10)
    task.advance(4)
    assert task.fraction_complete == pytest.approx(0.4)


def test_fraction_complete_at_completion() -> None:
    task = TrackedTask(name="t", total=10)
    task.advance(10)
    assert task.fraction_complete == 1.0


def test_fraction_complete_zero_total_returns_one() -> None:
    task = TrackedTask(name="t", total=0)
    assert task.fraction_complete == 1.0


def test_fraction_complete_capped_at_one() -> None:
    # Should never exceed 1.0 even if completed somehow exceeds total.
    task = TrackedTask(name="t", total=10, completed=10)
    task.completed = 15  # set directly, bypassing advance()
    assert task.fraction_complete == 1.0
