import logging

from uwtools.logging import setup_logging as _setup_logging
from uwtools.logging import use_logger as _use_logger


def use_custom_logger(logger: logging.Logger) -> None:
    """
    ???
    """
    _use_logger(logger=logger)


def use_uwtools_logger(quiet: bool = False, verbose: bool = False) -> None:
    """
    ???
    """
    _setup_logging(quiet=quiet, verbose=verbose)
