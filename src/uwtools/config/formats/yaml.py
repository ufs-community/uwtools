from __future__ import annotations

from types import SimpleNamespace as ns
from typing import TYPE_CHECKING

import yaml

from uwtools.config.formats.base import Config
from uwtools.config.support import (
    INCLUDE_TAG,
    add_yaml_representers,
    dict_to_yaml_str,
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

    @staticmethod
    def _depth_ok(depth: int) -> bool:
        """
        Is the given config depth compatible with this format?
        """
        return depth >= 0

    @classmethod
    def _dict_to_str(cls, cfg: dict) -> str:
        """
        Return the YAML representation of the given dict.

        :param cfg: The in-memory config object.
        """
        add_yaml_representers()
        return dict_to_yaml_str(cfg)

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
