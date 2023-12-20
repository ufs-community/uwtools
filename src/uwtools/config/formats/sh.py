import re
import shlex
from io import StringIO
from typing import Optional, Union

from uwtools.config.formats.base import Config
from uwtools.config.tools import config_check_depths_dump
from uwtools.logging import log
from uwtools.utils.file import FORMAT, OptionalPath, readable, writable


class SHConfig(Config):
    """
    Concrete class to handle bash config files.
    """

    def __init__(self, config: Union[dict, OptionalPath] = None):
        """
        Construct a SHConfig object.

        :param config: Config file to load (None => read from stdin), or initial dict.
        """
        super().__init__(config)
        self.parse_include()

    # Private methods

    def _load(self, config_file: OptionalPath) -> dict:
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

    def dump(self, path: OptionalPath) -> None:
        """
        Dumps the config as key=value lines.

        :param path: Path to dump config to.
        """
        config_check_depths_dump(config_obj=self, target_format=FORMAT.sh)
        self.dump_dict(path, self.data)

    @staticmethod
    def dump_dict(path: OptionalPath, cfg: dict) -> None:
        """
        Dumps a provided config dictionary in bash format.

        :param path: Path to dump config to.
        :param cfg: The in-memory config object to dump.
        """

        # Write first to a StringIO object to avoid creating a partial file in case of problems
        # rendering or quoting config values.

        config_check_depths_dump(config_obj=cfg, target_format=FORMAT.sh)
        s = StringIO()
        for key, value in cfg.items():
            print("%s=%s" % (key, shlex.quote(str(value))), file=s)
        with writable(path) as f:
            print(s.getvalue().strip(), file=f)
        s.close()

    @staticmethod
    def get_depth_threshold() -> Optional[int]:
        """
        Returns the config's depth threshold.
        """
        return 1

    @staticmethod
    def get_format() -> str:
        """
        Returns the config's format name.
        """
        return FORMAT.sh
