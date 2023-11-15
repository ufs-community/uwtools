from collections import OrderedDict
from types import SimpleNamespace as ns
from typing import Optional

import f90nml

from uwtools.config.formats.base import Config
from uwtools.utils.file import OptionalPath, readable, writable


class NMLConfig(Config):
    """
    Concrete class to handle Fortran namelist files.
    """

    def __init__(self, config_file) -> None:
        super().__init__(config_file)
        self.parse_include()

    # Private methods

    def _load(self, config_file: OptionalPath) -> dict:
        """
        Reads and parses a Fortran namelist file.

        See docs for Config._load().

        :param config_file: Path to config file to load.
        """

        # f90nml returns OrderedDict objects to maintain the order of namelists in the namelist
        # files that it reads. But in Python 3.6+ the standard dict maintains order as well. Since
        # OrderedDict can cause problems downstream when serializing to YAML, convert OrderedDict
        # objects to standard dicts here.

        def from_od(d):
            return {key: from_od(val) if isinstance(val, dict) else val for key, val in d.items()}

        with readable(config_file) as f:
            return from_od(f90nml.read(f).todict())

    # Public methods

    def dump(self, path: OptionalPath) -> None:
        """
        Dumps the config in Fortran namelist format.

        :param path: Path to dump config to.
        """
        NMLConfig.dump_dict(path, self.data)

    @staticmethod
    def dump_dict(path: OptionalPath, cfg: dict, opts: Optional[ns] = None) -> None:
        """
        Dumps a provided config dictionary in Fortran namelist format.

        :param path: Path to dump config to.
        :param cfg: The in-memory config object to dump.
        :param opts: Other options required by a subclass.
        """

        # f90nml honors namelist and variable order if it receives an OrderedDict as input, so
        # ensure that it receives one.

        def to_od(d):
            return OrderedDict(
                {key: to_od(val) if isinstance(val, dict) else val for key, val in d.items()}
            )

        with writable(path) as f:
            f90nml.Namelist(to_od(cfg)).write(f, sort=False)
