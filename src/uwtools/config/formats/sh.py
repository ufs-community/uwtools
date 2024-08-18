import re
import shlex
from pathlib import Path
from typing import Optional, Union

from uwtools.config.formats.base import Config
from uwtools.config.tools import config_check_depths_dump
from uwtools.logging import log
from uwtools.strings import FORMAT
from uwtools.utils.file import readable, writable


class SHConfig(Config):
    """
    Concrete class to handle bash config files.
    """

    def __init__(self, config: Union[dict, Optional[Path]] = None):
        """
        Construct a SHConfig object.

        :param config: Config file to load (None => read from stdin), or initial dict.
        """
        super().__init__(config)
        self._parse_include()

    # Private methods

    @classmethod
    def _dict_to_str(cls, cfg: dict) -> str:
        """
        Returns the field-table representation of the given dict.

        :param cfg: A dict object.
        """
        config_check_depths_dump(config_obj=cfg, target_format=FORMAT.sh)
        lines = []
        for key, value in cfg.items():
            lines.append("%s=%s" % (key, shlex.quote(str(value))))
        return "\n".join(lines)

    @staticmethod
    def _get_depth_threshold() -> Optional[int]:
        """
        Returns the config's depth threshold.
        """
        return 1

    @staticmethod
    def _get_format() -> str:
        """
        Returns the config's format name.
        """
        return FORMAT.sh

    def _load(self, config_file: Optional[Path]) -> dict:
        """
        Reads and parses key=value lines from shell code.

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
                log.debug(f"Read variable '{var}' with value '{val}'")
            else:
                log.debug(f"Ignoring: {s}")
        return d

    # Public methods

    def dump(self, path: Optional[Path]) -> None:
        """
        Dumps the config as key=value lines.

        :param path: Path to dump config to (default: stdout).
        """
        config_check_depths_dump(config_obj=self, target_format=FORMAT.sh)
        self.dump_dict(self.data, path)

    @classmethod
    def dump_dict(cls, cfg: dict, path: Optional[Path] = None) -> None:
        """
        Dumps a provided config dictionary in bash format.

        :param cfg: The in-memory config object to dump.
        :param path: Path to dump config to (default: stdout).
        """
        with writable(path) as f:
            print(cls._dict_to_str(cfg), file=f)
