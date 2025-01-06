from __future__ import annotations

import math
from collections import OrderedDict
from datetime import datetime
from functools import partial
from importlib import import_module
from typing import Callable, Type, Union

import yaml

from uwtools.exceptions import UWConfigError
from uwtools.logging import log
from uwtools.strings import FORMAT

INCLUDE_TAG = "!include"
YAMLKey = Union[bool, float, int, str]

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


def uw_yaml_loader() -> type[yaml.SafeLoader]:
    """
    A loader with basic UW constructors added.
    """
    loader = yaml.SafeLoader
    for tag_class in (UWYAMLConvert, UWYAMLRemove):
        for tag in getattr(tag_class, "TAGS"):
            loader.add_constructor(tag, tag_class)
    return loader


def dict_to_yaml_str(d: dict, sort: bool = False) -> str:
    """
    Return a uwtools-conventional YAML representation of the given dict.

    :param d: A dict object.
    :param sort: Sort dict/mapping keys?
    """
    return yaml.dump(d, default_flow_style=False, indent=2, sort_keys=sort, width=math.inf).strip()


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

    TAGS = ("!bool", "!datetime", "!dict", "!float", "!int", "!list")
    ValT = Union[bool, datetime, dict, float, int, list]

    def __init__(self, loader: yaml.SafeLoader, node: yaml.nodes.ScalarNode) -> None:
        super().__init__(loader, node)
        if not isinstance(self.value, str):
            hint = (
                "%s %s" % (node.tag, node.value)
                if node.start_mark is None
                else node.start_mark.buffer.replace("\n\x00", "")
            )
            raise UWConfigError(
                "Value tagged %s must be type 'str' (not '%s') in: %s"
                % (node.tag, node.value.__class__.__name__, hint)
            )

    def __repr__(self) -> str:
        return "%s %s" % (self.tag, self.converted)

    def __str__(self) -> str:
        return str(self.converted)

    @property
    def converted(self) -> UWYAMLConvert.ValT:
        """
        Return the original YAML value converted to the type speficied by the tag.

        :raises: Appropriate exception if the value cannot be represented as the required type.
        """
        load_as = lambda t, v: t(yaml.safe_load(v))
        converters: list[Callable[..., UWYAMLConvert.ValT]] = [
            partial(load_as, bool),
            datetime.fromisoformat,
            partial(load_as, dict),
            float,
            int,
            partial(load_as, list),
        ]
        return dict(zip(UWYAMLConvert.TAGS, converters))[self.tag](self.value)


class UWYAMLRemove(UWYAMLTag):
    """
    A class supporting a custom YAML tag to remove a YAML key/value pair.

    The constructor implements the interface required by a pyyaml Loader object's add_consructor()
    method. See the pyyaml documentation for details.
    """

    TAGS = ("!remove",)
