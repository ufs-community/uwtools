"""
A UPP common mixin class.
"""

from __future__ import annotations

from pathlib import Path
from typing import ClassVar

from iotaa import tasks

from uwtools.utils.tasks import filecopy


class UPPCommon:
    """
    A UPP common mixin class.
    """

    # Facts specific to the supported UPP version:

    GENPROCTYPE_IDX = 8
    NFIELDS = 16
    NPARAMS = 42

    # Task methods:

    @tasks
    def control_file(self):
        """
        The GRIB control file.
        """
        yield self.taskname("GRIB control file")
        yield filecopy(
            src=Path(self.config["control_file"]), dst=self.rundir / "postxconfig-NT.txt"
        )

    # Helper methods:

    @property
    def namelist_path(self) -> Path:
        """
        The path to the namelist file.
        """
        return self.rundir / "itag"

    # Placeholders to be overridden by mixing-in classes:

    config: ClassVar = {}

    @property
    def rundir(self) -> Path:
        return Path("/dev/null")

    def taskname(self, _: str | None = None) -> str:
        return "NA"
