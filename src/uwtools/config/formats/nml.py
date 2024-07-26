from collections import OrderedDict
from io import StringIO
from pathlib import Path
from typing import Optional, Union

import f90nml  # type: ignore
from f90nml import Namelist

from uwtools.config.formats.base import Config
from uwtools.config.tools import config_check_depths_dump
from uwtools.strings import FORMAT
from uwtools.utils.file import readable, writable


class NMLConfig(Config):
    """
    Concrete class to handle Fortran namelist files.
    """

    def __init__(self, config: Union[dict, Optional[Path]] = None) -> None:
        """
        Construct an NMLConfig object.

        :param config: Config file to load (None => read from stdin), or initial dict.
        """
        super().__init__(config)
        self.parse_include()

    # Private methods

    @classmethod
    def _dict_to_str(cls, cfg: dict) -> str:
        """
        Returns the field-table representation of the given dict.

        :param cfg: A dict object.
        """

        def to_od(d):
            return OrderedDict(
                {key: to_od(val) if isinstance(val, dict) else val for key, val in d.items()}
            )

        config_check_depths_dump(config_obj=cfg, target_format=FORMAT.nml)
        nml: Namelist = Namelist(to_od(cfg)) if not isinstance(cfg, Namelist) else cfg
        with StringIO() as sio:
            nml.write(sio, sort=False)
            return sio.getvalue().strip()

    def _load(self, config_file: Optional[Path]) -> dict:
        """
        Reads and parses a Fortran namelist file.

        See docs for Config._load().

        :param config_file: Path to config file to load.
        """
        with readable(config_file) as f:
            config: dict = f90nml.read(f)
            return config

    # Public methods

    def dump(self, path: Optional[Path]) -> None:
        """
        Dumps the config in Fortran namelist format.

        :param path: Path to dump config to.
        """
        self.dump_dict(cfg=self.data, path=path)

    @classmethod
    def dump_dict(cls, cfg: Union[dict, Namelist], path: Optional[Path] = None) -> None:
        """
        Dumps a provided config dictionary in Fortran namelist format.

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
        return None

    @staticmethod
    def get_format() -> str:
        """
        Returns the config's format name.
        """
        return FORMAT.nml
