# pylint: disable=duplicate-code
import configparser
from io import StringIO
from types import SimpleNamespace as ns
from typing import Optional

from uwtools.config.formats.base import Config
from uwtools.config.support import config_sections, depth
from uwtools.utils.file import OptionalPath, readable, writable


class INIConfig(Config):
    """
    Concrete class to handle INI config files.
    """

    _MAXDEPTH = 2

    def __init__(
        self,
        config_file: str,
    ):
        """
        Construct an INIConfig object.

        Spaces may be included for INI format, but should be excluded for bash.

        :param config_file: Path to the config file to load.
        """
        super().__init__(config_file)
        self.parse_include()

    # Private methods

    def _load(self, config_file: OptionalPath) -> dict:
        """
        Reads and parses an INI file.

        See docs for Config._load().

        :param config_file: Path to config file to load.
        """
        cfg = configparser.ConfigParser()
        sections = config_sections(cfg)
        with readable(config_file) as f:
            raw = f.read()
            cfg.read_string(raw)
            return sections

    # Public methods

    def dump(self, path: OptionalPath) -> None:
        """
        Dumps the config in INI format.

        :param path: Path to dump config to.
        """
        INIConfig.dump_dict(path, self.data, space=True)

    @staticmethod
    def dump_dict(path: OptionalPath, cfg: dict, opts: Optional[ns] = None, **kwargs) -> None:
        """
        Dumps a provided config dictionary in INI format.

        :param path: Path to dump config to.
        :param cfg: The in-memory config object to dump.
        :param space_around_delimiters: Place spaces around delimiters?
        """
        # Configparser adds a newline after each section, presumably to create nice-looking output
        # when an INI contains multiple sections. Unfortunately, it also adds a newline after the
        # _final_ section, resulting in an anomalous trailing newline. To avoid this, write first to
        # memory, then strip the trailing newline.
        assert depth(cfg) == INIConfig._MAXDEPTH

        parser = configparser.ConfigParser()
        s = StringIO()
        parser.read_dict(cfg)
        parser.write(s, space_around_delimiters=kwargs.get("space", True))
        with writable(path) as f:
            print(s.getvalue().strip(), file=f)
        s.close()
