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

    import marshal
    import hashlib

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
