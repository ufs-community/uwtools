from __future__ import annotations

import re
import shlex
from typing import TYPE_CHECKING

from uwtools.config.formats.base import Config
from uwtools.config.tools import config_check_depths_dump
from uwtools.logging import log
from uwtools.strings import FORMAT
from uwtools.utils.file import readable, writable

if TYPE_CHECKING:
    from pathlib import Path


class SHConfig(Config):
    """
    Work with key=value shell configs.
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
        return depth == 1

    @classmethod
    def _dict_to_str(cls, cfg: dict) -> str:
        """
        Return the field-table representation of the given dict.

        :param cfg: A dict object.
        """
        config_check_depths_dump(config_obj=cfg, target_format=FORMAT.sh)
        lines = []
        for key, value in cfg.items():
            lines.append("%s=%s" % (key, shlex.quote(str(value))))
        return "\n".join(lines)

    @staticmethod
    def _get_format() -> str:
        """
        Return the config's format name.
        """
        return FORMAT.sh

    def _load(self, config_file: Path | None) -> dict:
        """
        Read and parse key=value lines from shell code.

        See docs for Config._load().

        :param config_file: Path to config file to load.
        """
        with readable(config_file) as f:
            strings = shlex.split(f.read(), comments=True)
        d = {}
        for s in strings:
            if m := re.match(r"^([a-zA-Z_]+[a-zA-Z0-9_]*)=(.*)$", s):
                var, val = m[1], m[2]
                d[var] = val
                log.debug("Read variable '%s' with value '%s'", var, val)
            else:
                log.debug("Ignoring: %s", s)
        return d

    # Public methods

    def as_dict(self) -> dict:
        """
        Returns a pure dict version of the config.
        """
        return self.data

    def dump(self, path: Path | None) -> None:
        """
        Dump the config as key=value lines.

        :param path: Path to dump config to (default: stdout).
        """
        config_check_depths_dump(config_obj=self, target_format=FORMAT.sh)
        self.dump_dict(self.data, path)

    @classmethod
    def dump_dict(cls, cfg: dict, path: Path | None = None) -> None:
        """
        Dump a provided config dictionary in bash format.

        :param cfg: The in-memory config object to dump.
        :param path: Path to dump config to (default: stdout).
        """
        with writable(path) as f:
            print(cls._dict_to_str(cfg), file=f)
