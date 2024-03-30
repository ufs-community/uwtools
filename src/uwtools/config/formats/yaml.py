from pathlib import Path
from types import SimpleNamespace as ns
from typing import Optional

import yaml

from uwtools.config.formats.base import Config
from uwtools.config.support import (
    INCLUDE_TAG,
    UWYAMLConvert,
    UWYAMLRemove,
    add_yaml_representers,
    log_and_error,
)
from uwtools.strings import FORMAT
from uwtools.utils.file import readable, writable

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
    Concrete class to handle YAML config files.
    """

    def __repr__(self) -> str:
        """
        The string representation of a YAMLConfig object.
        """
        add_yaml_representers()
        return yaml.dump(self.data, default_flow_style=False).strip()

    # Private methods

    def _load(self, config_file: Optional[Path]) -> dict:
        """
        Reads and parses a YAML file.

        See docs for Config._load().

        :param config_file: Path to config file to load.
        """
        loader = self._yaml_loader
        with readable(config_file) as f:
            try:
                config = yaml.load(f.read(), Loader=loader)
                assert isinstance(config, dict)
                return config
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
        Returns a dictionary with include tags processed.

        :param loader: The YAML loader.
        :param node: A YAML node.
        """
        filepaths = loader.construct_sequence(node)
        return self._load_paths(filepaths)

    @property
    def _yaml_loader(self) -> type[yaml.SafeLoader]:
        """
        Set up the loader with the appropriate constructors.
        """
        loader = yaml.SafeLoader
        loader.add_constructor(INCLUDE_TAG, self._yaml_include)
        for tag_class in (UWYAMLConvert, UWYAMLRemove):
            for tag in getattr(tag_class, "TAGS"):
                loader.add_constructor(tag, tag_class)
        return loader

    # Public methods

    def dump(self, path: Optional[Path] = None) -> None:
        """
        Dumps the config in YAML format.

        :param path: Path to dump config to.
        """
        self.dump_dict(self.data, path)

    @staticmethod
    def dump_dict(cfg: dict, path: Optional[Path] = None) -> None:
        """
        Dumps a provided config dictionary in YAML format.

        :param cfg: The in-memory config object to dump.
        :param path: Path to dump config to.
        """
        add_yaml_representers()
        with writable(path) as f:
            yaml.dump(cfg, f, sort_keys=False)

    @staticmethod
    def get_depth_threshold() -> Optional[int]:
        """
        Returns the config's depth threshold.
        """
        return None

    @staticmethod
    def get_format() -> str:
        """
        Returns the config's format name.
        """
        return FORMAT.yaml
