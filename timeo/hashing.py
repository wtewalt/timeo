"""
hashing — stable bytecode-based hash for function cache keys.
"""

from __future__ import annotations

import hashlib
import marshal
from typing import Callable, Any


def hash_function(fn: Callable[..., Any]) -> str:
    """Return a SHA-256 hex digest of the function's full code object.

    Uses marshal.dumps(fn.__code__) to capture the complete code object —
    including constants, variable names, and nested code objects — so the
    hash changes whenever the function's implementation changes.
    """
    code_bytes = marshal.dumps(fn.__code__)
    return hashlib.sha256(code_bytes).hexdigest()
