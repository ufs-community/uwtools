"""
Helpers to be used when parsing arguments and gathering config files.
"""

import logging
import sys
from pathlib import Path
from typing import Dict, List


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
    logging.error(msg)
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

        print(msg, file=sys.stderr)
        raise FileNotFoundError(msg)
    return str(p.absolute())
