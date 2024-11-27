from __future__ import annotations

import math
from collections import OrderedDict
from datetime import datetime
from importlib import import_module
from typing import Callable, Type, Union

import yaml

from uwtools.exceptions import UWConfigError
from uwtools.logging import log
from uwtools.strings import FORMAT

INCLUDE_TAG = "!include"


# Public functions


def depth(d: dict) -> int:
    """
    The depth of a dictionary.

    :param d: The dictionary whose depth to calculate.
    :return: The length of the longest path to a value in the dictionary.
    """
    return (max(map(depth, d.values()), default=0) + 1) if isinstance(d, dict) else 0


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
    cfgclass: Type = getattr(import_module(f"uwtools.config.formats.{fmt}"), lookup[fmt])
    return cfgclass


def from_od(d: Union[OrderedDict, dict]) -> dict:
    """
    Return a (nested) dict with content equivalent to the given (nested) OrderedDict.

    :param d: A (possibly nested) OrderedDict.
    """
    return {key: from_od(val) if isinstance(val, dict) else val for key, val in d.items()}


def log_and_error(msg: str) -> Exception:
    """
    Log an error message and return an exception for the caller to potentially raise.

    :param msg: The error message to log and to associate with raised exception.
    :return: An exception containing the same error message.
    """
    log.error(msg)
    return UWConfigError(msg)


def walk_key_path(config: dict, key_path: list[str]) -> tuple[dict, str]:
    """
    Navigate to the sub-config at the end of the path of given keys.

    :param config: A config.
    :param key_path: Path of keys to subsection of config file.
    :return: The sub-config and a string representation of the key path.
    """
    keys = []
    pathstr = "<unknown>"
    for key in key_path:
        keys.append(key)
        pathstr = ".".join(keys)
        try:
            subconfig = config[key]
        except KeyError as e:
            raise log_and_error(f"Bad config path: {pathstr}") from e
        if not isinstance(subconfig, dict):
            raise log_and_error(f"Value at {pathstr} must be a dictionary")
        config = subconfig
    return config, pathstr


def yaml_to_str(cfg: dict) -> str:
    """
    Return a uwtools-conventional YAML representation of the given dict.

    :param cfg: A dict object.
    """
    return yaml.dump(cfg, default_flow_style=False, sort_keys=False, width=math.inf).strip()


class UWYAMLTag:
    """
    A base class for custom UW YAML tags.
    """

    def __init__(self, _: yaml.SafeLoader, node: yaml.nodes.ScalarNode) -> None:
        self.tag: str = node.tag
        self.value: str = node.value

    def __repr__(self) -> str:
        return ("%s %s" % (self.tag, self.value)).strip()

    @staticmethod
    def represent(dumper: yaml.Dumper, data: UWYAMLTag) -> yaml.nodes.ScalarNode:
        """
        Serialize a tagged scalar as "!type value".

        Implements the interface required by pyyaml's add_representer() function. See the pyyaml
        documentation for details.
        """
        return dumper.represent_scalar(data.tag, data.value)


class UWYAMLConvert(UWYAMLTag):
    """
    A class supporting custom YAML tags specifying type conversions.

    The constructor implements the interface required by a pyyaml Loader object's add_consructor()
    method. See the pyyaml documentation for details.
    """

    TAGS = ("!bool", "!datetime", "!float", "!int")

    def convert(self) -> Union[datetime, float, int]:
        """
        Return the original YAML value converted to the specified type.

        Will raise an exception if the value cannot be represented as the specified type.
        """
        converters: dict[
            str, Union[Callable[[str], bool], Callable[[str], datetime], type[float], type[int]]
        ] = dict(
            zip(
                self.TAGS,
                [lambda x: {"True": True, "False": False}[x], datetime.fromisoformat, float, int],
            )
        )
        return converters[self.tag](self.value)


class UWYAMLRemove(UWYAMLTag):
    """
    A class supporting a custom YAML tag to remove a YAML key/value pair.

    The constructor implements the interface required by a pyyaml Loader object's add_consructor()
    method. See the pyyaml documentation for details.
    """

    TAGS = ("!remove",)
