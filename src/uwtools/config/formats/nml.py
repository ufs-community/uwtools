from collections import OrderedDict
from typing import Optional, Union

import f90nml  # type: ignore
from f90nml import Namelist

from uwtools.config.formats.base import Config
from uwtools.config.tools import config_check_depths_dump
from uwtools.utils.file import FORMAT, OptionalPath, readable, writable


class NMLConfig(Config):
    """
    Concrete class to handle Fortran namelist files.
    """

    def __init__(self, config: Union[dict, OptionalPath] = None) -> None:
        """
        Construct an NMLConfig object.

        :param config: Config file to load (None => read from stdin), or initial dict.
        """
        super().__init__(config)
        self.parse_include()

    # Private methods

    def _load(self, config_file: OptionalPath) -> dict:
        """
        Reads and parses a Fortran namelist file.

        See docs for Config._load().

        :param config_file: Path to config file to load.
        """
        with readable(config_file) as f:
            config: dict = f90nml.read(f)
            return config

    # Public methods

    def dump(self, path: OptionalPath) -> None:
        """
        Dumps the config in Fortran namelist format.

        :param path: Path to dump config to.
        """
        self.dump_dict(cfg=self.data, path=path)

    @staticmethod
    def dump_dict(cfg: Union[dict, Namelist], path: OptionalPath = None) -> None:
        """
        Dumps a provided config dictionary in Fortran namelist format.

        :param cfg: The in-memory config object to dump.
        :param path: Path to dump config to.
        """

        def to_od(d):
            return OrderedDict(
                {key: to_od(val) if isinstance(val, dict) else val for key, val in d.items()}
            )

        config_check_depths_dump(config_obj=cfg, target_format=FORMAT.nml)
        nml: Namelist = Namelist(to_od(cfg)) if not isinstance(cfg, Namelist) else cfg
        with writable(path) as f:
            nml.write(f, sort=False)

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
        return FORMAT.nml
