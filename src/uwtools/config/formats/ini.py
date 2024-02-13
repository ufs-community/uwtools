import configparser
from io import StringIO
from typing import Optional, Union

from uwtools.config.formats.base import Config
from uwtools.config.tools import config_check_depths_dump
from uwtools.utils.file import FORMAT, OptionalPath, readable, writable


class INIConfig(Config):
    """
    Concrete class to handle INI config files.
    """

    def __init__(self, config: Union[dict, OptionalPath] = None):
        """
        Construct an INIConfig object.

        :param config: Config file to load (None => read from stdin), or initial dict.
        """
        super().__init__(config)
        self.parse_include()

    # Private methods

    def _load(self, config_file: OptionalPath) -> dict:
        """
        Reads and parses an INI file.

        See docs for Config._load().

        :param config_file: Path to config file to load.
        """
        cfg = configparser.ConfigParser()
        with readable(config_file) as f:
            cfg.read_string(f.read())
        return {s: dict(cfg[s].items()) for s in cfg.sections()}

    # Public methods

    def dump(self, path: OptionalPath = None) -> None:
        """
        Dumps the config in INI format.

        :param path: Path to dump config to.
        """
        config_check_depths_dump(config_obj=self, target_format=FORMAT.ini)

        self.dump_dict(self.data, path)

    @staticmethod
    def dump_dict(cfg: dict, path: OptionalPath = None) -> None:
        """
        Dumps a provided config dictionary in INI format.

        :param cfg: The in-memory config object to dump.
        :param path: Path to dump config to.
        """

        # Configparser adds a newline after each section, presumably to create nice-looking output
        # when an INI contains multiple sections. Unfortunately, it also adds a newline after the
        # _final_ section, resulting in an anomalous trailing newline. To avoid this, write first to
        # memory, then strip the trailing newline.

        config_check_depths_dump(config_obj=cfg, target_format=FORMAT.ini)
        parser = configparser.ConfigParser()
        s = StringIO()
        parser.read_dict(cfg)
        parser.write(s)
        with writable(path) as f:
            print(s.getvalue().strip(), file=f)
        s.close()

    @staticmethod
    def get_depth_threshold() -> Optional[int]:
        """
        Returns the config's depth threshold.
        """
        return 2

    @staticmethod
    def get_format() -> str:
        """
        Returns the config's format name.
        """
        return FORMAT.ini
