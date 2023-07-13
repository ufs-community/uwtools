"""
Helpers to be used when parsing arguments and gathering config files.
"""

import argparse
import logging
import os
import pathlib
from typing import Optional

from uwtools.logger import Logger


def dict_from_config_args(args):
    """
    Given a list of command line arguments in the form key=value, return a dictionary of key/value
    pairs.
    """
    return dict([arg.split("=") for arg in args])


def get_file_type(arg):
    """
    Returns a standardized file type given the suffix of the input arg.
    """

    suffix = pathlib.Path(arg).suffix
    if suffix in [".yaml", ".yml"]:
        return "YAML"
    if suffix in [".bash", ".sh", ".ini", ".cfg"]:
        return "INI"
    if suffix in [".nml"]:
        return "F90"
    msg = f"Bad file suffix -- {suffix}. Cannot determine file type!"
    logging.critical(msg)
    raise ValueError(msg)


def path_if_file_exists(arg):
    """
    Checks whether a file exists, and returns the path if it does.
    """
    if not os.path.exists(arg):
        msg = f"{arg} does not exist!"
        raise argparse.ArgumentTypeError(msg)

    return os.path.abspath(arg)


def setup_logging(
    log_file: str,
    log_name: Optional[str] = None,
    quiet: bool = False,
    verbose: bool = False,
    color: bool = False,
) -> Logger:
    """
    Create the Logger object.
    """

    log = Logger(
        colored_log=color,
        fmt=None if verbose else "%(message)s",
        level="debug" if verbose else "info",
        log_file=log_file,
        quiet=quiet,
        name=log_name,
    )
    log.debug(f"Finished setting up debug file logging in {log_file}")
    return log
