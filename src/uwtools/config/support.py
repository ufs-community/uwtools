from __future__ import annotations

from importlib import import_module
from typing import Dict, Type, Union

import yaml

from uwtools.exceptions import UWConfigError
from uwtools.logging import log
from uwtools.utils.file import FORMAT

INCLUDE_TAG = "!INCLUDE"


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


class TaggedScalar:
    """
    PM WRITEME.
    """

    TAGS = ("!bool", "!float", "!int", "!str")

    def __init__(self, _: yaml.SafeLoader, node: yaml.nodes.ScalarNode) -> None:
        self.tag: str = node.tag
        self.value: str = node.value

    def convert(self) -> Union[bool, float, int, str]:
        """
        PM WRITEME.
        """
        converters: Dict[str, type] = dict(zip(self.TAGS, [bool, float, int, str]))
        return converters[self.tag](self.value)

    @staticmethod
    def represent(dumper: yaml.Dumper, data: TaggedScalar) -> yaml.nodes.ScalarNode:
        """
        PM WRITEME.
        """
        return dumper.represent_scalar(data.tag, data.value)
