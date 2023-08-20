"""
Logging support.
"""

import logging
import os
import sys


def setup_logging(quiet: bool = False, verbose: bool = False) -> None:
    """
    Set up logging.

    :param quiet: Supress all logging output.
    :param verbose: Log all messages.
    """
    if quiet and verbose:
        print("Speficy at most one of 'quiet' and 'verbose'", file=sys.stderr)
        sys.exit(1)
    logging.basicConfig(
        **{
            "datefmt": "%Y-%m-%dT%H:%M:%S",
            "format": '[%(asctime)s] %(levelname)8s %(message)s',
            "level": logging.DEBUG if verbose else logging.INFO,
            **({"filename": os.devnull} if quiet else {"stream": sys.stderr}),
        }
    )
