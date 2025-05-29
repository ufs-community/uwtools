"""
An assets driver for UPP.
"""

from pathlib import Path

from iotaa import tasks

from uwtools.drivers.driver import AssetsCycleLeadtimeBased
from uwtools.drivers.support import set_driver_docstring
from uwtools.drivers.upp_common import UPPCommon
from uwtools.exceptions import UWConfigError
from uwtools.strings import STR


class UPPAssets(AssetsCycleLeadtimeBased, UPPCommon):
    """
    An assets driver for UPP.
    """

    # Workflow tasks

    @tasks
    def provisioned_rundir(self):
        """
        Run directory provisioned with all required content.
        """
        yield self.taskname("provisioned run directory")
        yield [
            self.control_file(),
            self.files_copied(),
            self.files_linked(),
            self.namelist_file(),
        ]

    # Public helper methods

    @classmethod
    def driver_name(cls) -> str:
        """
        The name of this driver.
        """
        return STR.upp_assets

    @property
    def output(self) -> dict[str, list[Path]]:
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


set_driver_docstring(UPPAssets)
