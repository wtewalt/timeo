"""
hashing — stable bytecode-based hash for function cache keys.

hash_function() accepts an optional depends_on list (approach B).  When
provided, the bytecode of every listed callable is included in the digest so
that a change to any dependency invalidates the cache key automatically.
"""

from __future__ import annotations

import hashlib
import marshal
from typing import Any, Callable


def hash_function(
    fn: Callable[..., Any],
    depends_on: list[Callable[..., Any]] | None = None,
) -> str:
    """Return a SHA-256 hex digest of the function's full code object.

    Uses marshal.dumps(fn.__code__) to capture the complete code object —
    including constants, variable names, and nested code objects — so the
    hash changes whenever the function's implementation changes.

    Args:
        fn: The primary function to hash.
        depends_on: Optional list of additional callables whose bytecode should
            be included in the digest.  Use this when ``fn`` calls helper
            functions whose changes should invalidate the cache key::

                @timeo.track(learn=True, depends_on=[helper_fn])
                def top_function():
                    helper_fn()

            If any function in *depends_on* changes, the resulting hash
            changes and learn-mode resets automatically.
    """
    h = hashlib.sha256()
    h.update(marshal.dumps(fn.__code__))
    for dep in depends_on or []:
        h.update(marshal.dumps(dep.__code__))
    return h.hexdigest()
