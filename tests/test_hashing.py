"""Tests for timeo/hashing.py — function bytecode hashing."""

from timeo.hashing import hash_function


def test_same_function_same_hash() -> None:
    def my_func() -> int:
        return 42

    assert hash_function(my_func) == hash_function(my_func)


def test_different_functions_different_hash() -> None:
    def func_a() -> int:
        return 1

    def func_b() -> int:
        return 2

    assert hash_function(func_a) != hash_function(func_b)


def test_modified_function_different_hash() -> None:
    # Compile two code objects with different bodies and compare their hashes.
    code_a = compile("def f(): return 1", "<string>", "exec")
    code_b = compile("def f(): return 2", "<string>", "exec")

    import hashlib
    import marshal

    hash_a = hashlib.sha256(marshal.dumps(code_a)).hexdigest()
    hash_b = hashlib.sha256(marshal.dumps(code_b)).hexdigest()

    assert hash_a != hash_b


def test_hash_is_hex_string() -> None:
    def my_func() -> None:
        pass

    result = hash_function(my_func)
    assert isinstance(result, str)
    assert len(result) == 64  # SHA-256 hex digest is always 64 chars
    int(result, 16)  # raises ValueError if not valid hex


# ---------------------------------------------------------------------------
# Approach B — depends_on
# ---------------------------------------------------------------------------


def test_depends_on_none_same_as_no_deps() -> None:
    """Passing depends_on=None is identical to not passing it."""

    def fn() -> int:
        return 1

    assert hash_function(fn) == hash_function(fn, depends_on=None)


def test_depends_on_empty_list_same_as_no_deps() -> None:
    def fn() -> int:
        return 1

    assert hash_function(fn) == hash_function(fn, depends_on=[])


def test_depends_on_changes_hash() -> None:
    """Adding a dependency should produce a different hash."""

    def top() -> None:
        pass

    def dep() -> None:
        pass

    assert hash_function(top) != hash_function(top, depends_on=[dep])


def test_depends_on_different_dep_different_hash() -> None:
    """Two different dependency functions produce two different hashes."""

    def top() -> None:
        pass

    def dep_a() -> int:
        return 1

    def dep_b() -> int:
        return 2

    hash_a = hash_function(top, depends_on=[dep_a])
    hash_b = hash_function(top, depends_on=[dep_b])
    assert hash_a != hash_b


def test_depends_on_dep_change_invalidates_hash() -> None:
    """Simulates a nested function changing: the hash for top must change."""

    def top() -> None:
        pass

    def nested_v1() -> int:
        return 1

    def nested_v2() -> int:
        return 2  # implementation changed

    hash_before = hash_function(top, depends_on=[nested_v1])
    hash_after = hash_function(top, depends_on=[nested_v2])
    assert hash_before != hash_after


def test_depends_on_order_matters() -> None:
    """Dependency order is significant — [a, b] != [b, a]."""

    def top() -> None:
        pass

    def dep_a() -> int:
        return 1

    def dep_b() -> int:
        return 2

    hash_ab = hash_function(top, depends_on=[dep_a, dep_b])
    hash_ba = hash_function(top, depends_on=[dep_b, dep_a])
    assert hash_ab != hash_ba


def test_depends_on_stable_across_calls() -> None:
    """The same function + deps always produces the same hash."""

    def top() -> None:
        pass

    def dep() -> int:
        return 99

    assert hash_function(top, depends_on=[dep]) == hash_function(top, depends_on=[dep])
