from __future__ import annotations

from collections import OrderedDict
from io import StringIO
from typing import TYPE_CHECKING

import f90nml  # type: ignore[import-untyped]
from f90nml import Namelist

from uwtools.config.formats.base import Config
from uwtools.config.support import from_od
from uwtools.config.tools import validate_depth
from uwtools.strings import FORMAT
from uwtools.utils.file import readable, writable

if TYPE_CHECKING:
    from pathlib import Path


class NMLConfig(Config):
    """
    Work with Fortran namelist configs.
    """

    def __init__(self, config: dict | Path | None = None) -> None:
        """
        Construct an NMLConfig object.

        :param config: Config file to load (None => read from stdin), or initial dict.
        """
        super().__init__(config)
        self._parse_include()

    # Private methods

    @staticmethod
    def _depth_ok(depth: int) -> bool:
        """
        Is the given config depth compatible with this format?
        """

        # Fortran namelist configs must be at least depth 2, as they must have levels for namelist
        # names as well as keys (Fortran variables). The depth upper bound is harder to quantify:
        # Derived-typed component references in namelists may reference any number of intermediate
        # components, and each intermediate component is reflected as a YAML mapping. For example,
        # the namelist
        #
        #   &a b%c%d%e%f = 42 /
        #
        # is represented in YAML as
        #
        #   a: {b: {c: {d: {e: {f: 42}}}}}
        #
        # per f90nml. uwtools can map back and forth between these formats, but it should be clear
        # that a ceiling cannot be defined for the YAML depth.

        return depth >= 2  # noqa: PLR2004

    @classmethod
    def _dict_to_str(cls, cfg: dict) -> str:
        """
        Return the field-table representation of the given dict.

        :param cfg: A dict object.
        """

        def to_od(d: dict):
            return OrderedDict(
                {key: to_od(val) if isinstance(val, dict) else val for key, val in d.items()}
            )

        validate_depth(cfg, FORMAT.nml)
        nml: Namelist = Namelist(to_od(cfg)) if not isinstance(cfg, Namelist) else cfg
        with StringIO() as sio:
            nml.write(sio, sort=False)
            return sio.getvalue().strip()

    @staticmethod
    def _get_format() -> str:
        """
        Return the config's format name.
        """
        return FORMAT.nml

    def _load(self, config_file: Path | None) -> dict:
        """
        Read and parse a Fortran namelist file.

        See docs for Config._load().

        :param config_file: Path to config file to load.
        :return: The parsed namelist data.
        """
        with readable(config_file) as f:
            config: dict = f90nml.read(f)
            return config

    # Public methods

    def as_dict(self) -> dict:
        """
        Returns a pure dict version of the config.
        """
        d = self.data
        return from_od(d.todict()) if isinstance(d, Namelist) else d

    def dump(self, path: Path | None) -> None:
        """
        Dump the config in Fortran namelist format.

        :param path: Path to dump config to (default: stdout).
        """
        self.dump_dict(cfg=self.data, path=path)

    @classmethod
    def dump_dict(cls, cfg: dict | Namelist, path: Path | None = None) -> None:
        """
        Dump a provided config dictionary in Fortran namelist format.

        :param cfg: The in-memory config object to dump.
        :param path: Path to dump config to (default: stdout).
        """
        with writable(path) as f:
            print(cls._dict_to_str(cfg), file=f)
