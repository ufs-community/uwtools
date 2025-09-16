from __future__ import annotations

import configparser
from io import StringIO
from typing import TYPE_CHECKING

from uwtools.config.formats.base import Config
from uwtools.config.tools import validate_depth
from uwtools.strings import FORMAT
from uwtools.utils.file import readable, writable

if TYPE_CHECKING:
    from pathlib import Path


class INIConfig(Config):
    """
    Work with INI configs.
    """

    def __init__(self, config: dict | Path | None = None):
        """
        :param config: Config file to load (None => read from stdin), or initial dict.
        """
        super().__init__(config)
        self._parse_include()

    # Private methods

    @staticmethod
    def _depth_ok(depth: int) -> bool:
        """
        Is the given config depth compatible with this format?
        """

        # INI configs have one level for the [section], and one level for each key, so are exactly
        # depth 2.

        return depth == 2  # noqa: PLR2004

    @classmethod
    def _dict_to_str(cls, cfg: dict) -> str:
        """
        Return the INI representation of the given dict.

        :param cfg: A dict object.
        """

        # Configparser adds a newline after each section, presumably to create nice-looking output
        # when an INI contains multiple sections. Unfortunately, it also adds a newline after the
        # _final_ section, resulting in an anomalous trailing newline. To avoid this, write first to
        # memory, then strip the trailing newline.

        validate_depth(cfg, FORMAT.ini)
        parser = configparser.ConfigParser()
        parser.read_dict(cfg)
        with StringIO() as sio:
            parser.write(sio)
            return sio.getvalue().strip()

    @staticmethod
    def _get_format() -> str:
        """
        Return the config's format name.
        """
        return FORMAT.ini

    def _load(self, config_file: Path | None) -> dict:
        """
        Read and parse an INI file.

        See docs for Config._load().

        :param config_file: Path to config file to load.
        """
        cfg = configparser.ConfigParser()
        with readable(config_file) as f:
            cfg.read_string(f.read())
        return {s: dict(cfg[s].items()) for s in cfg.sections()}

    # Public methods

    def as_dict(self) -> dict:
        """
        Returns a pure dict version of the config.
        """
        return self.data

    def dump(self, path: Path | None = None) -> None:
        """
        Dump the config in INI format.

        :param path: Path to dump config to (default: stdout).
        """
        self.dump_dict(self.data, path)

    @classmethod
    def dump_dict(cls, cfg: dict, path: Path | None = None) -> None:
        """
        Dump a provided config dictionary in INI format.

        :param cfg: The in-memory config object to dump.
        :param path: Path to dump config to (default: stdout).
        """
        with writable(path) as f:
            print(cls._dict_to_str(cfg), file=f)
