from __future__ import annotations

from collections import OrderedDict
from datetime import datetime, timedelta
from types import SimpleNamespace as ns
from typing import TYPE_CHECKING

import yaml
from f90nml import Namelist  # type: ignore[import-untyped]

from uwtools.config.formats.base import Config
from uwtools.config.support import (
    INCLUDE_TAG,
    UWYAMLConvert,
    UWYAMLGlob,
    UWYAMLRemove,
    dict_to_yaml_str,
    from_od,
    log_and_error,
    uw_yaml_loader,
)
from uwtools.exceptions import UWConfigError
from uwtools.strings import FORMAT
from uwtools.utils.file import readable, writable

if TYPE_CHECKING:
    from pathlib import Path

_MSGS = ns(
    unhashable="""
ERROR:
The input config file may contain a Jinja2 templated value at the location listed above. Ensure the
value is enclosed in quotes.
""".strip(),
    unregistered_constructor="""
ERROR:
The input config file contains a constructor that is not registered with the uwtools package.

constructor: {constructor}
config file: {config_file}

Define the constructor before proceeding.
""".strip(),
    unregistered_filter="""
ERROR:
The input config file contains a Jinja2 filter that is not registered with the uwtools package.

filter: {filter}
key: {key}

Define the filter before proceeding.
""".strip(),
)


class YAMLConfig(Config):
    """
    Work with YAML configs.
    """

    # Private methods

    @classmethod
    def _add_yaml_representers(cls) -> None:
        """
        Add representers to the YAML dumper for custom types.
        """
        yaml.add_representer(Namelist, cls._represent_namelist)
        yaml.add_representer(OrderedDict, cls._represent_ordereddict)
        yaml.add_representer(
            datetime,
            lambda dumper, data: dumper.represent_scalar(
                "tag:yaml.org,2002:str", data.strftime("%Y-%m-%dT%H:%M:%S")
            ),
        )
        yaml.add_representer(
            timedelta,
            lambda dumper, data: dumper.represent_scalar("!timedelta", str(data)),
        )
        for tag_class in [UWYAMLConvert, UWYAMLGlob, UWYAMLRemove]:
            yaml.add_representer(tag_class, tag_class.represent)

    @classmethod
    def _dict_to_str(cls, cfg: dict) -> str:
        """
        Return the YAML representation of the given dict.

        :param cfg: The in-memory config object.
        """
        cls._add_yaml_representers()
        return dict_to_yaml_str(cfg)

    @staticmethod
    def _get_depth_threshold() -> int | None:
        """
        Return the config's depth threshold.
        """
        return None

    @staticmethod
    def _get_format() -> str:
        """
        Return the config's format name.
        """
        return FORMAT.yaml

    def _load(self, config_file: Path | None) -> dict:
        """
        Read and parse a YAML file.

        See docs for Config._load().

        :param config_file: Path to config file to load.
        """
        with readable(config_file) as f:
            try:
                config = yaml.load(f.read(), Loader=self._yaml_loader)
                if isinstance(config, dict):
                    return config
                t = type(config).__name__
                msg = "Parsed a%s %s value from %s, expected a dict" % (
                    "n" if t[0] in "aeiou" else "",
                    t,
                    config_file or "stdin",
                )
                raise UWConfigError(msg)
            except yaml.constructor.ConstructorError as e:
                if e.problem:
                    if "unhashable" in e.problem:
                        msg = _MSGS.unhashable
                    else:
                        constructor = e.problem.split()[-1]
                        msg = _MSGS.unregistered_constructor.format(
                            config_file=config_file, constructor=constructor
                        )
                else:
                    msg = str(e)
                raise log_and_error(msg) from e

    @classmethod
    def _represent_namelist(cls, dumper: yaml.Dumper, data: Namelist) -> yaml.nodes.MappingNode:
        """
        Convert an f90nml Namelist to an OrderedDict, then represent as a YAML mapping.

        :param dumper: The YAML dumper.
        :param data: The f90nml Namelist to serialize.
        :return: A YAML mapping.
        """
        namelist_dict = data.todict()
        return dumper.represent_mapping("tag:yaml.org,2002:map", namelist_dict)

    @classmethod
    def _represent_ordereddict(
        cls, dumper: yaml.Dumper, data: OrderedDict
    ) -> yaml.nodes.MappingNode:
        """
        Recursrively convert an OrderedDict to a dict, then represent as a YAML mapping.

        :param dumper: The YAML dumper.
        :param data: The OrderedDict to serialize.
        :return: A YAML mapping.
        """

        return dumper.represent_mapping("tag:yaml.org,2002:map", from_od(data))

    def _yaml_include(self, loader: yaml.Loader, node: yaml.SequenceNode) -> dict:
        """
        Return a dictionary with include tags processed.

        :param loader: The YAML loader.
        :param node: A YAML node.
        """
        filepaths = loader.construct_sequence(node)
        return self._load_paths(filepaths)

    @property
    def _yaml_loader(self) -> type[yaml.SafeLoader]:
        """
        A loader with all UW constructors added.
        """
        loader = uw_yaml_loader()
        loader.add_constructor(INCLUDE_TAG, self._yaml_include)
        return loader

    # Public methods

    def as_dict(self) -> dict:
        """
        Returns a pure dict version of the config.
        """
        return self.data

    def dump(self, path: Path | None = None) -> None:
        """
        Dump the config in YAML format.

        :param path: Path to dump config to (default: stdout).
        """
        self.dump_dict(self.data, path)

    @classmethod
    def dump_dict(cls, cfg: dict, path: Path | None = None) -> None:
        """
        Dump a provided config dictionary in YAML format.

        :param cfg: The in-memory config object to dump.
        :param path: Path to dump config to (default: stdout).
        """
        with writable(path) as f:
            print(cls._dict_to_str(cfg), file=f)


def _write_plain_open_ended(self: yaml.emitter.Emitter, *args, **kwargs) -> None:
    """
    Write YAML without the "..." end-of-stream marker.
    """
    self.write_plain_base(*args, **kwargs)  # type: ignore[attr-defined]
    self.open_ended = False


setattr(yaml.emitter.Emitter, "write_plain_base", yaml.emitter.Emitter.write_plain)
setattr(yaml.emitter.Emitter, "write_plain", _write_plain_open_ended)
