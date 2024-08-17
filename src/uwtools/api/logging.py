"""
API access to ``uwtools`` logging logic.
"""

import logging

from uwtools.logging import setup_logging as _setup_logging
from uwtools.logging import use_logger as _use_logger


def use_custom_logger(logger: logging.Logger) -> None:
    """
    Log to the specified ``Logger`` object, configured according to your needs.

    :param logger: The custom logger to use.
    """
    _use_logger(logger=logger)


def use_uwtools_logger(quiet: bool = False, verbose: bool = False) -> None:
    """
    Log to a ``Logger`` configured to follow ``uwtools`` conventions.

    :param quiet: Supress all logging output.
    :param verbose: Log all messages.
    """
    _setup_logging(quiet=quiet, verbose=verbose)
