import configparser
from io import StringIO
from types import SimpleNamespace as ns
from typing import Optional

from uwtools.config.formats.base import Config
from uwtools.config.support import depth
from uwtools.utils.file import OptionalPath, readable, writable


class INIConfig(Config):
    """
    Concrete class to handle INI config files.
    """

    def __init__(
        self,
        config_file: str,
        space_around_delimiters: bool = True,
    ):
        """
        Construct an INIConfig object.

        Spaces may be included for INI format, but should be excluded for bash.

        :param config_file: Path to the config file to load.
        :param space_around_delimiters: Include spaces around delimiters?
        """
        super().__init__(config_file)
        self.space_around_delimiters = space_around_delimiters
        self.parse_include()

    # Private methods

    def _load(self, config_file: OptionalPath) -> dict:
        """
        Reads and parses an INI file.

        See docs for Config._load().

        :param config_file: Path to config file to load.
        """
        # The protected _sections method is the most straightforward way to get at the dict
        # representation of the parse config.

        cfg = configparser.ConfigParser()
        cfg.optionxform = str  # type: ignore
        sections = cfg._sections  # type: ignore # pylint: disable=protected-access
        with readable(config_file) as f:
            raw = f.read()
        try:
            cfg.read_string(raw)
            return dict(sections)
        except configparser.MissingSectionHeaderError:
            cfg.read_string("[top]\n" + raw)
            return dict(sections.get("top"))

    # Public methods

    def dump(self, path: OptionalPath) -> None:
        """
        Dumps the config in INI format.

        :param path: Path to dump config to.
        """
        INIConfig.dump_dict(path, self.data, ns(space=self.space_around_delimiters))

    @staticmethod
    def dump_dict(path: OptionalPath, cfg: dict, opts: Optional[ns] = None) -> None:
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
        parser = configparser.ConfigParser()
        s = StringIO()
        cfgdepth = depth(cfg)
        assert cfgdepth in (1, 2)  # 2 => .ini
        parser.read_dict(cfg)
        parser.write(s, space_around_delimiters=opts.space if opts else True)
        with writable(path) as f:
            print(s.getvalue().strip(), file=f)
        s.close()
