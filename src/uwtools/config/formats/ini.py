# pylint: disable=duplicate-code
import configparser
from io import StringIO

from uwtools.config.formats.base import Config
from uwtools.utils.file import OptionalPath, readable, writable


class INIConfig(Config):
    """
    Concrete class to handle INI config files.
    """

    DEPTH = 2

    def __init__(
        self,
        config_file: str,
    ):
        """
        Construct an INIConfig object.

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
        with readable(config_file) as f:
            cfg.read_string(f.read())
        return {s: dict(cfg[s].items()) for s in cfg.sections()}

    # Public methods

    def dump(self, path: OptionalPath) -> None:
        """
        Dumps the config in INI format.

        :param path: Path to dump config to.
        """
        self.dump_dict(path, self.data)

    @staticmethod
    def dump_dict(path: OptionalPath, cfg: dict) -> None:
        """
        Dumps a provided config dictionary in INI format.

        :param path: Path to dump config to.
        :param cfg: The in-memory config object to dump.
        """
        # Configparser adds a newline after each section, presumably to create nice-looking output
        # when an INI contains multiple sections. Unfortunately, it also adds a newline after the
        # _final_ section, resulting in an anomalous trailing newline. To avoid this, write first to
        # memory, then strip the trailing newline.

        parser = configparser.ConfigParser()
        s = StringIO()
        parser.read_dict(cfg)
        parser.write(s)
        with writable(path) as f:
            print(s.getvalue().strip(), file=f)
        s.close()
