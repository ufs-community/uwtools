# pylint: disable=duplicate-code
import configparser
from io import StringIO

from uwtools.config.formats.base import Config
from uwtools.config.tools import config_check_depths_dump
from uwtools.utils.file import FORMAT, OptionalPath, readable, writable


class SHConfig(Config):
    """
    Concrete class to handle bash config files.
    """

    DEPTH = 1

    def __init__(
        self,
        config_file: str,
    ):
        """
        Construct a SHConfig object.

        :param config_file: Path to the config file to load.
        """
        super().__init__(config_file)
        self.parse_include()

    # Private methods

    def _load(self, config_file: OptionalPath) -> dict:
        """
        Reads and parses shell code consisting solely of key=value lines.

        See docs for Config._load().

        :param config_file: Path to config file to load.
        """
        cfg = configparser.ConfigParser()
        section = "top"
        with readable(config_file) as f:
            cfg.read_string(f"[{section}]\n" + f.read())
        return dict(cfg[section].items())

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

        config_check_depths_dump(config_obj=cfg, target_format=FORMAT.sh)

        s = StringIO()
        for key, value in cfg.items():
            print(f"{key}={value}", file=s)
        with writable(path) as f:
            print(s.getvalue().strip(), file=f)
        s.close()
