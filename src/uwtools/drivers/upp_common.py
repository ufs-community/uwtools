"""
A UPP common mixin class.
"""

from __future__ import annotations

from datetime import timedelta
from pathlib import Path
from typing import TYPE_CHECKING, ClassVar

from iotaa import asset, task, tasks

from uwtools.config.formats.nml import NMLConfig
from uwtools.exceptions import UWConfigError
from uwtools.strings import STR
from uwtools.utils.tasks import file, filecopy, symlink

if TYPE_CHECKING:
    from uwtools.config.formats.base import Config
    from uwtools.config.support import YAMLKey


class UPPCommon:
    """
    A UPP common mixin class.
    """

    # Facts specific to the supported UPP version:

    GENPROCTYPE_IDX = 8
    NFIELDS = 16
    NPARAMS = 42

    # Workflow tasks:

    @tasks
    def control_file(self):
        """
        The GRIB control file.
        """
        yield self.taskname("GRIB control file")
        yield filecopy(
            src=Path(self.config["control_file"]), dst=self.rundir / "postxconfig-NT.txt"
        )

    @tasks
    def files_copied(self):
        """
        Files copied for run.
        """
        yield self.taskname("files copied")
        yield [
            filecopy(src=Path(src), dst=self.rundir / dst)
            for dst, src in self.config.get("files_to_copy", {}).items()
        ]

    @tasks
    def files_linked(self):
        """
        Files linked for run.
        """
        yield self.taskname("files linked")
        yield [
            symlink(target=Path(target), linkname=self.rundir / linkname)
            for linkname, target in self.config.get("files_to_link", {}).items()
        ]

    @task
    def namelist_file(self):
        """
        The namelist file.
        """
        path = self.namelist_path
        yield self.taskname(str(path))
        yield asset(path, path.is_file)
        base_file = self.config[STR.namelist].get(STR.basefile)
        yield file(Path(base_file)) if base_file else None
        self._create_user_updated_config(
            config_class=NMLConfig,
            config_values=self.config[STR.namelist],
            path=path,
            schema=self.namelist_schema(),
        )

    # Helper methods:

    @property
    def namelist_path(self) -> Path:
        """
        The path to the namelist file.
        """
        return self.rundir / "itag"

    @property
    def output(self) -> dict[str, Path] | dict[str, list[Path]]:
        """
        Returns a description of the file(s) created when this component runs.
        """
        # Read the control file into an array of lines. Get the number of blocks (one per output
        # GRIB file) and the number of variables per block. For each block, construct a filename
        # from the block's identifier and the suffix defined above.
        cf = self.config["control_file"]
        try:
            lines = Path(cf).read_text().split("\n")
        except (FileNotFoundError, PermissionError) as e:
            msg = f"Could not open UPP control file {cf}"
            raise UWConfigError(msg) from e
        suffix = ".GrbF%02d" % int(self.leadtime.total_seconds() / 3600)
        nblocks, lines = int(lines[0]), lines[1:]
        nvars, lines = list(map(int, lines[:nblocks])), lines[nblocks:]
        paths = []
        for _ in range(nblocks):
            identifier = lines[0]
            paths.append(self.rundir / (identifier + suffix))
            fields, lines = lines[: self.NFIELDS], lines[self.NFIELDS :]
            _, lines = (
                (lines[0], lines[1:])
                if fields[self.GENPROCTYPE_IDX] == "ens_fcst"
                else (None, lines)
            )
            lines = lines[self.NPARAMS * nvars.pop() :]
        return {"paths": paths}

    # Placeholders to appease linter/typechecker, to be overridden by client classes:

    config: ClassVar = {}

    @staticmethod
    def _create_user_updated_config(
        config_class: type[Config], config_values: dict, path: Path, schema: dict | None = None
    ) -> None:
        pass

    @property
    def leadtime(self):
        return timedelta(seconds=0)

    def namelist_schema(
        self, _config_keys: list[YAMLKey] | None = None, _schema_keys: list[str] | None = None
    ) -> dict:
        return {}

    @property
    def rundir(self) -> Path:
        return Path("/dev/null")

    def taskname(self, _: str | None = None) -> str:
        return "NA"
