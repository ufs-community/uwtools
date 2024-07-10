import configparser
from io import StringIO
from pathlib import Path
from typing import Optional, Union

from uwtools.config.formats.base import Config
from uwtools.config.tools import config_check_depths_dump
from uwtools.strings import FORMAT
from uwtools.utils.file import readable, writable


class INIConfig(Config):
    """
    Concrete class to handle INI config files.
    """

    def __init__(self, config: Union[dict, Optional[Path]] = None):
        """
        Construct an INIConfig object.

        :param config: Config file to load (None => read from stdin), or initial dict.
        """
        super().__init__(config)
        self.parse_include()

    # Private methods

    @classmethod
    def _dict_to_str(cls, cfg: dict) -> str:
        """
        Returns the INI representation of the given dict.

        :param cfg: A dict object.
        """

        # Configparser adds a newline after each section, presumably to create nice-looking output
        # when an INI contains multiple sections. Unfortunately, it also adds a newline after the
        # _final_ section, resulting in an anomalous trailing newline. To avoid this, write first to
        # memory, then strip the trailing newline.

        config_check_depths_dump(config_obj=cfg, target_format=FORMAT.ini)
        parser = configparser.ConfigParser()
        sio = StringIO()
        parser.read_dict(cfg)
        parser.write(sio)
        s = sio.getvalue().strip()
        sio.close()
        return s

    def _load(self, config_file: Optional[Path]) -> dict:
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

    def dump(self, path: Optional[Path] = None) -> None:
        """
        Dumps the config in INI format.

        :param path: Path to dump config to.
        """
        self.dump_dict(self.data, path)

    @classmethod
    def dump_dict(cls, cfg: dict, path: Optional[Path] = None) -> None:
        """
        Dumps a provided config dictionary in INI format.

        :param cfg: The in-memory config object to dump.
        :param path: Path to dump config to.
        """
        with writable(path) as f:
            print(cls._dict_to_str(cfg), file=f)

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
