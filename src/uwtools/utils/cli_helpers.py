"""

Helpers to be used when parsing arguments and gathering config files

"""

import argparse
import logging
import os
import pathlib

from uwtools.logger import Logger


def dict_from_config_args(args):  # pylint: disable=unused-variable
    """Given a list of command line arguments in the form key=value, return a
    dictionary of key/value pairs."""
    return dict([arg.split("=") for arg in args])


def get_file_type(arg):  # pylint: disable=unused-variable
    """Returns a standardized file type given the suffix of the input
    arg."""

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


def path_if_file_exists(arg):  # pylint: disable=unused-variable
    """Checks whether a file exists, and returns the path if it does."""
    if not os.path.exists(arg):
        msg = f"{arg} does not exist!"
        raise argparse.ArgumentTypeError(msg)

    return os.path.abspath(arg)


def setup_logging(user_args, log_name=None):  # pylint: disable=unused-variable
    """Create the Logger object"""

    log = Logger(
        colored_log=bool(user_args.verbose),
        fmt=None if user_args.verbose else "%(message)s",
        level="debug" if user_args.verbose else "info",
        log_file=user_args.log_file,
        quiet=user_args.quiet,
        name=log_name,
    )
    log.debug(f"Finished setting up debug file logging in {user_args.log_file}")
    return log
