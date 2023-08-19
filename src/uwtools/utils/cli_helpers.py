"""
Helpers to be used when parsing arguments and gathering config files.
"""

import logging
from pathlib import Path
from typing import Dict, List, Optional

from uwtools.logger import Logger


def dict_from_key_eq_val_strings(config_items: List[str]) -> Dict[str, str]:
    """
    Given a list of key=value strings, return a dictionary of key/value pairs.

    :param config_items: Strings in the form key=value.
    :return: A dictionary based on the input key=value strings.
    """
    return dict([arg.split("=") for arg in config_items])


def get_file_type(path: str) -> str:
    """
    Returns a standardized file type given a path/filename.

    :param path: A path or filename.
    :return: One of a set of supported file types.
    :raises: ValueError if the path/filename suffix is unrecognized.
    """

    suffix = Path(path).suffix
    if suffix in [".yaml", ".yml"]:
        return "YAML"
    if suffix in [".bash", ".sh", ".ini", ".cfg"]:
        return "INI"
    if suffix in [".nml"]:
        return "F90"
    msg = f"Bad file suffix -- {suffix}. Cannot determine file type!"
    logging.critical(msg)
    raise ValueError(msg)


def path_if_it_exists(path: str) -> str:
    """
    Returns the given path as an absolute path if it exists, and raises an exception otherwise.

    :param path: The filesystem path to test.
    :return: The same filesystem path as an absolute path.
    :raises: FileNotFoundError is path does not exst
    """
    p = Path(path)
    if not p.exists():
        msg = f"{path} does not exist"
        logging.critical(msg)
        raise FileNotFoundError(msg)
    return str(p.absolute())


def setup_logging(
    log_file: str,
    log_name: Optional[str] = None,
    quiet: bool = False,
    verbose: bool = False,
    color: bool = False,
) -> Logger:
    """
    Return a configured Logger object.

    :param log_file: Path to the file to log to.
    :param log_name: Name associated with log messages.
    :param quiet: Suppress logging.
    :param verbose: Log in verbose mode.
    :param color: Log in color?
    :return: A configured Logger object.
    """
    logger = Logger(
        colored_log=color,
        fmt=None if verbose else "%(message)s",
        level="debug" if verbose else "info",
        log_file=log_file,
        quiet=quiet,
        name=log_name,
    )
    logger.debug(f"Finished setting up debug file logging in {log_file}")
    return logger
