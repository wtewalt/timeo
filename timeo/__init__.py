"""
timeo — terminal progress bars via decorators.
"""

from timeo.decorator import advance, iter, track
from timeo.manager import ProgressManager as _ProgressManager


def live():
    """Context manager for explicit display lifecycle control.

    Usage::

        with timeo.live():
            process_files(my_files)
            download_data(my_urls)
    """
    return _ProgressManager.get().live()


__all__ = ["track", "advance", "iter", "live"]
