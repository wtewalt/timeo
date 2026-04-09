"""Tests for timeo/decorator.py — track, advance, iter."""

import pytest

from timeo.decorator import _current_task, _infer_total, advance
from timeo.decorator import iter as timeo_iter
from timeo.decorator import track


# ---------------------------------------------------------------------------
# _infer_total
# ---------------------------------------------------------------------------


def test_infer_total_from_list() -> None:
    assert _infer_total([1, 2, 3]) == 3


def test_infer_total_from_first_sized_arg() -> None:
    assert _infer_total("hello", [1, 2]) == 5  # str is Sized; len("hello") == 5


def test_infer_total_from_kwarg() -> None:
    assert _infer_total(items=[1, 2, 3, 4]) == 4


def test_infer_total_none_when_no_sized_arg() -> None:
    assert _infer_total(42, 3.14) is None


def test_infer_total_none_for_no_args() -> None:
    assert _infer_total() is None


# ---------------------------------------------------------------------------
# @timeo.track — basic behaviour
# ---------------------------------------------------------------------------


def test_track_calls_wrapped_function(mocker) -> None:
    mocker.patch("timeo.decorator.ProgressManager")
    called_with = []

    @track
    def my_func(x: int) -> int:
        called_with.append(x)
        return x * 2

    result = my_func(5)
    assert result == 10
    assert called_with == [5]


def test_track_preserves_function_name(mocker) -> None:
    mocker.patch("timeo.decorator.ProgressManager")

    @track
    def my_named_func() -> None:
        pass

    assert my_named_func.__name__ == "my_named_func"


def test_track_parameterized_form_works(mocker) -> None:
    mocker.patch("timeo.decorator.ProgressManager")

    @track(learn=False)
    def my_func() -> str:
        return "ok"

    assert my_func() == "ok"


def test_context_var_reset_on_exception(mocker) -> None:
    mocker.patch("timeo.decorator.ProgressManager")

    @track
    def failing_func() -> None:
        raise ValueError("boom")

    with pytest.raises(ValueError):
        failing_func()

    assert _current_task.get() is None


def test_context_var_reset_on_success(mocker) -> None:
    mocker.patch("timeo.decorator.ProgressManager")

    @track
    def ok_func() -> None:
        pass

    ok_func()
    assert _current_task.get() is None


# ---------------------------------------------------------------------------
# advance()
# ---------------------------------------------------------------------------


def test_advance_noop_outside_tracked_function() -> None:
    # Should not raise even when called with no active task.
    advance()
    advance(5)


def test_advance_updates_current_task(mocker) -> None:
    mock_manager = mocker.patch("timeo.decorator.ProgressManager")

    @track
    def my_func(items: list) -> None:
        advance(2)

    my_func([1, 2, 3])

    mock_manager.get.return_value.advance_task.assert_called()


# ---------------------------------------------------------------------------
# iter()
# ---------------------------------------------------------------------------


def test_iter_yields_all_items(mocker) -> None:
    mocker.patch("timeo.decorator.ProgressManager")

    @track
    def my_func(items: list) -> list:
        return list(timeo_iter(items))

    result = my_func([10, 20, 30])
    assert result == [10, 20, 30]


def test_iter_auto_advances(mocker) -> None:
    mock_manager = mocker.patch("timeo.decorator.ProgressManager")

    @track
    def my_func(items: list) -> None:
        for _ in timeo_iter(items):
            pass

    my_func([1, 2, 3])

    # advance_task should have been called once per item.
    assert mock_manager.get.return_value.advance_task.call_count == 3
