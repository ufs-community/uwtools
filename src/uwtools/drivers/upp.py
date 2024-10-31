"""
A driver for UPP.
"""

from math import log10
from pathlib import Path

from iotaa import asset, task, tasks

from uwtools.config.formats.nml import NMLConfig
from uwtools.drivers.driver import DriverCycleLeadtimeBased, OutputT
from uwtools.drivers.support import set_driver_docstring
from uwtools.exceptions import UWConfigError
from uwtools.strings import STR
from uwtools.utils.tasks import file, filecopy, symlink


class UPP(DriverCycleLeadtimeBased):
    """
    A driver for UPP.
    """

    # Facts specific to the supported UPP version:

    FIELDS_PER_BLOCK = 16
    GEN_PROC_TYPE_IDX = 8
    PARAMS_PER_VAR = 42

    # Workflow tasks

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
        path = self._namelist_path
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
            self.runscript(),
        ]

    # Public helper methods

    @classmethod
    def driver_name(cls) -> str:
        """
        The name of this driver.
        """
        return STR.upp

    @property
    def output(self) -> OutputT:
        """
        Returns a description of the file(s) created when this component runs.
        """
        # Derive values from the current driver config. GRIB output filename suffixes include the
        # forecast leadtime, zero-padded to at least 2 digits (more if necessary). Avoid taking the
        # log of zero.
        cf = self.config["control_file"]
        leadtime = int(self.leadtime.total_seconds() / 3600)
        suffix = ".GrbF%0{}d".format(max(2, int(log10(leadtime or 1)) + 1)) % leadtime
        # Read the control file into an array of lines. Get the number of blocks (one per output
        # GRIB file) and the number of variables per block. For each block, construct a filename
        # from the block's identifier and the suffix defined above.
        try:
            with open(cf, "r", encoding="utf-8") as f:
                cfg = f.read().split("\n")
        except (FileNotFoundError, PermissionError) as e:
            raise UWConfigError(f"Could not open UPP control file {cf}") from e
        nblocks, cfg = int(cfg[0]), cfg[1:]
        nvars, cfg = list(map(int, cfg[:nblocks])), cfg[nblocks:]
        paths = []
        for _ in range(nblocks):
            identifier = cfg[0]
            paths.append(str(self.rundir / (identifier + suffix)))
            fields, cfg = cfg[: self.FIELDS_PER_BLOCK], cfg[self.FIELDS_PER_BLOCK :]
            _, cfg = (
                (cfg[0], cfg[1:]) if fields[self.GEN_PROC_TYPE_IDX] == "ens_fcst" else (None, cfg)
            )
            cfg = cfg[self.PARAMS_PER_VAR * nvars.pop() :]
        return {"gribfiles": paths}

    # Private helper methods

    @property
    def _namelist_path(self) -> Path:
        """
        The path to the namelist file.
        """
        return self.rundir / "itag"

    @property
    def _runcmd(self) -> str:
        """
        The full command-line component invocation.
        """
        execution = self.config.get(STR.execution, {})
        mpiargs = execution.get(STR.mpiargs, [])
        components = [
            execution.get(STR.mpicmd),
            *[str(x) for x in mpiargs],
            "%s < %s" % (execution[STR.executable], self._namelist_path.name),
        ]
        return " ".join(filter(None, components))


set_driver_docstring(UPP)
