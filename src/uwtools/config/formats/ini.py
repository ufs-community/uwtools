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
    Work with INI configs.
    """

    def __init__(self, config: Union[dict, Optional[Path]] = None):
        """
        :param config: Config file to load (None => read from stdin), or initial dict.
        """
        super().__init__(config)
        self._parse_include()

    # Private methods

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

        config_check_depths_dump(config_obj=cfg, target_format=FORMAT.ini)
        parser = configparser.ConfigParser()
        parser.read_dict(cfg)
        with StringIO() as sio:
            parser.write(sio)
            return sio.getvalue().strip()

    @staticmethod
    def _get_depth_threshold() -> Optional[int]:
        """
        Return the config's depth threshold.
        """
        return 2

    @staticmethod
    def _get_format() -> str:
        """
        Return the config's format name.
        """
        return FORMAT.ini

    def _load(self, config_file: Optional[Path]) -> dict:
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

    def dump(self, path: Optional[Path] = None) -> None:
        """
        Dump the config in INI format.

        :param path: Path to dump config to (default: stdout).
        """
        self.dump_dict(self.data, path)

    @classmethod
    def dump_dict(cls, cfg: dict, path: Optional[Path] = None) -> None:
        """
        Dump a provided config dictionary in INI format.

        :param cfg: The in-memory config object to dump.
        :param path: Path to dump config to (default: stdout).
        """
        with writable(path) as f:
            print(cls._dict_to_str(cfg), file=f)
