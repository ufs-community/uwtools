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
        print("Specify at most one of 'quiet' and 'verbose'", file=sys.stderr)
        sys.exit(1)
    logging.basicConfig(
        **dict(
            (k, v)
            for k, v in [
                ("datefmt", "%Y-%m-%dT%H:%M:%S"),
                ("filename", os.devnull if quiet else None),
                ("format", "[%(asctime)s] %(levelname)8s %(message)s"),
                ("level", logging.DEBUG if verbose else logging.INFO),
                ("stream", None if quiet else sys.stderr),
            ]
            if v is not None
        )  # type: ignore
    )
