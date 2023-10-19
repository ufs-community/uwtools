"""
Logging support.
"""

import logging
import os
import sys

# The logging prefix
#
# [YYYY-MM-DDTHH:MM:HH]_CRITICAL_
# 1234567890123456789012345678901
#
# is 31 characters, leaving 69 for messages (e.g. separators) on a 100-character line.

MSGWIDTH = 69

log = logging.getLogger()  # default to Python base logger


def setup_logging(quiet: bool = False, verbose: bool = False) -> None:
    """
    Set up logging.

    :param quiet: Supress all logging output.
    :param verbose: Log all messages.
    """
    logger = logging.getLogger()
    for handler in logger.handlers:
        logger.removeHandler(handler)
    if quiet and verbose:
        print("Specify at most one of 'quiet' and 'verbose'", file=sys.stderr)
        sys.exit(1)
    kwargs: dict = {
        "datefmt": "%Y-%m-%dT%H:%M:%S",
        "format": "[%(asctime)s] %(levelname)8s %(message)s",
        "level": logging.DEBUG if verbose else logging.INFO,
        **({"filename": os.devnull} if quiet else {}),
    }
    logging.basicConfig(**kwargs)


def use_logger(logger: logging.Logger) -> None:
    """
    Log hereafter via the given logger.

    :param logger: The logger to log to.
    """
    global log  # pylint: disable=global-statement
    log = logger
