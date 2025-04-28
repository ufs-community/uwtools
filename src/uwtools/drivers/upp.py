"""
A driver for UPP.
"""

from pathlib import Path

from iotaa import asset, task, tasks

from uwtools.config.formats.nml import NMLConfig
from uwtools.drivers.driver import DriverCycleLeadtimeBased
from uwtools.drivers.support import set_driver_docstring
from uwtools.exceptions import UWConfigError
from uwtools.strings import STR
from uwtools.utils.tasks import file, filecopy, symlink


class UPP(DriverCycleLeadtimeBased):
    """
    A driver for UPP.
    """

    # Facts specific to the supported UPP version:

    GENPROCTYPE_IDX = 8
    NFIELDS = 16
    NPARAMS = 42

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
        return {"outputs": paths}

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
