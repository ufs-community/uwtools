# pylint: disable=duplicate-code
import configparser
from io import StringIO
from types import SimpleNamespace as ns
from typing import Optional

from uwtools.config.formats.base import Config
from uwtools.config.support import config_sections, depth
from uwtools.utils.file import OptionalPath, readable, writable


class SHConfig(Config):
    """
    Concrete class to handle bash config files.
    """

    _MAXDEPTH = 1

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
        Reads and parses a bash file.

        See docs for Config._load().

        :param config_file: Path to config file to load.
        """
        cfg = configparser.ConfigParser()
        sections = config_sections(cfg)
        with readable(config_file) as f:
            raw = f.read()
            cfg.read_string("[top]\n" + raw)
            return dict(sections.get("top"))

    # Public methods

    def dump(self, path: OptionalPath) -> None:
        """
        Dumps the config in bash format.

        :param path: Path to dump config to.
        """
        SHConfig.dump_dict(path, self.data, ns(space=False))

    @staticmethod
    def dump_dict(path: OptionalPath, cfg: dict, opts: Optional[ns] = None) -> None:
        """
        Dumps a provided config dictionary in bash format.

        :param path: Path to dump config to.
        :param cfg: The in-memory config object to dump.
        """
        assert depth(cfg) == SHConfig._MAXDEPTH

        s = StringIO()
        for key, value in cfg.items():
            print(f"{key}={value}", file=s)
        with writable(path) as f:
            print(s.getvalue().strip(), file=f)
        s.close()
