"""
A driver for UFS_UTILS's orog.
"""

from pathlib import Path

from iotaa import asset, external, task, tasks

from uwtools.drivers.driver import DriverTimeInvariant
from uwtools.drivers.stager import FileStager
from uwtools.drivers.support import set_driver_docstring
from uwtools.strings import STR
from uwtools.utils.file import writable


class Orog(DriverTimeInvariant, FileStager):
    """
    A driver for orog.
    """

    # Workflow tasks

    @external
    def grid_file(self):
        """
        The input grid file.
        """
        grid_file = Path(self.config["grid_file"])
        yield self.taskname(f"Input grid file {grid_file}")
        yield asset(grid_file, grid_file.is_file) if str(grid_file) != "none" else None

    @task
    def input_config_file(self):
        """
        The input config file.
        """
        path = self._input_config_path
        yield self.taskname(str(path))
        yield asset(path, path.is_file)
        yield self.grid_file()
        if inputs := self.config.get("old_line1_items"):
            ordered_entries = [
                "mtnres",
                "lonb",
                "latb",
                "jcap",
                "nr",
                "nf1",
                "nf2",
                "efac",
                "blat",
            ]
            inputs = " ".join([str(inputs[i]) for i in ordered_entries])
        outgrid = "'{}'".format(self.config["grid_file"])
        if orogfile := self.config.get("orog_file"):
            orogfile = "'{}'".format(orogfile)
        mask_only = ".true." if self.config.get("mask") else ".false."
        merge_file = self.config.get("merge", "none")  # string none is intentional
        content = [i for i in [inputs, outgrid, orogfile, mask_only, merge_file] if i is not None]
        with writable(path) as f:
            print("\n".join(content), file=f)

    @tasks
    def provisioned_rundir(self):
        """
        Run directory provisioned with all required content.
        """
        yield self.taskname("provisioned run directory")
        yield [
            self.files_copied(),
            self.files_hardlinked(),
            self.files_linked(),
            self.input_config_file(),
            self.runscript(),
        ]

    @task
    def runscript(self):
        """
        The runscript.
        """
        path = self._runscript_path
        yield self.taskname(path.name)
        yield asset(path, path.is_file)
        yield None
        envvars = {
            "KMP_AFFINITY": "disabled",
            "OMP_NUM_THREADS": self.config.get(STR.execution, {}).get(STR.threads, 1),
            "OMP_STACKSIZE": "2048m",
        }
        self._write_runscript(path=path, envvars=envvars)

    # Public helper methods

    @classmethod
    def driver_name(cls) -> str:
        """
        The name of this driver.
        """
        return STR.orog

    @property
    def output(self) -> dict[str, Path]:
        """
        Returns a description of the file(s) created when this component runs.
        """
        return {"path": self.rundir / "out.oro.nc"}

    # Private helper methods

    @property
    def _input_config_path(self) -> Path:
        """
        Path to the input config file.
        """
        return self.rundir / "orog.cfg"

    @property
    def _runcmd(self):
        """
        The full command-line component invocation.
        """
        executable = self.config[STR.execution][STR.executable]
        return "%s < %s" % (executable, self._input_config_path.name)


set_driver_docstring(Orog)
