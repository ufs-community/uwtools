"""
API access to ``uwtools`` logging logic.
"""

from uwtools.logging import setup_logging as _setup_logging


def use_uwtools_logger(quiet: bool = False, verbose: bool = False) -> None:
    """
    Log to a ``Logger`` configured to follow ``uwtools`` conventions.

    :param quiet: Supress all logging output.
    :param verbose: Log all messages.
    """
    _setup_logging(quiet=quiet, verbose=verbose)
