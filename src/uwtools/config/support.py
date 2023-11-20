import configparser
from importlib import import_module
from typing import Type

from uwtools.exceptions import UWConfigError
from uwtools.logging import log
from uwtools.utils.file import FORMAT

INCLUDE_TAG = "!INCLUDE"


def config_sections(config: configparser.ConfigParser):
    """
    Access the _sections method of a config object.

    :param config: The ConfigParser object
    :return: the _sections method of the ConfigParser object
    """
    # The protected _sections method is the most straightforward way to get at the dict
    # representation of the parse config.
    config.optionxform = str  # type: ignore
    return config._sections  # type: ignore # pylint: disable=protected-access


def depth(d: dict) -> int:
    """
    The depth of a dictionary.

    :param d: The dictionary whose depth to calculate.
    :return: The length of the longest path to a value in the dictionary.
    """
    return (max(map(depth, d.values())) + 1) if isinstance(d, dict) else 0


def format_to_config(fmt: str) -> Type:
    """
    Maps a CLI format name to its corresponding Config class.

    :param fmt: The format name as known to the CLI.
    :return: The appropriate Config class.
    """
    lookup = {
        FORMAT.fieldtable: "FieldTableConfig",
        FORMAT.ini: "INIConfig",
        FORMAT.nml: "NMLConfig",
        FORMAT.sh: "SHConfig",
        FORMAT.yaml: "YAMLConfig",
    }
    if not fmt in lookup:
        raise log_and_error("Format '%s' should be one of: %s" % (fmt, ", ".join(lookup)))
    return getattr(import_module(f"uwtools.config.formats.{fmt}"), lookup[fmt])


def log_and_error(msg: str) -> Exception:
    """
    Log an error message and return an exception for the caller to potentially raise.

    :param msg: The error message to log and to associate with raised exception.
    :return: An exception containing the same error message.
    """
    log.error(msg)
    return UWConfigError(msg)
