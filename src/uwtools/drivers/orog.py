"""
A driver for UFS_UTILS's orog.
"""

from pathlib import Path

from iotaa import asset, task, tasks

from uwtools.drivers.driver import DriverTimeInvariant
from uwtools.drivers.support import set_driver_docstring
from uwtools.strings import STR
from uwtools.utils.tasks import filecopy


class Orog(DriverTimeInvariant):
    """
    A driver for orog.
    """

    # Workflow tasks

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

    @external
    def grid_file(self):
        """
        The input grid file.
        """
        grid_file = self.config.get("grid_file")
        if grid_file is not None:
            path = Path(grid_file)
        yield self.taskname("Input grid file")
        yield asset(path, path.is_file) if grid_file else None

    @task
    def input_config_file(self):
        """
        The input config file.
        """
        path = self._input_config_path
        yield self.taskname(str(path))
        yield asset(path, path.is_file)
        yield self.grid_file()
        inputs = self.config.get("config")
        if inputs:
            inputs = " ".join(inputs.values())
        outgrid = self.config["grid_file"]
        orogfile = self.config.get("orog_file")
        mask_only = self.config.get("mask", False)
        merge_file = self.config.get("merge", "none") # string none is intentional
        content = [i for i in inputs, outgrid, orogfile, mask_only, merge_file if i is not None]
        with writable(path) as f:
            f.write("\n".join(content)

    @tasks
    def provisioned_rundir(self):
        """
        Run directory provisioned with all required content.
        """
        yield self.taskname("provisioned run directory")
        yield [
            self.files_copied(),
            self.input_config_file(),
            self.runscript(),
        ]

    # Public helper methods

    @property
    def driver_name(self) -> str:
        """
        Returns the name of this driver.
        """
        return STR.orog

    # Private helper methods

    @property
    def _input_config_path(self) -> Path:
        """
        Path to the input config file
        """
        return self.rundir / "INPS"

    @property
    def _runcmd(self):
        """
        Returns the full command-line component invocation.
        """
        executable = self.config[STR.execution][STR.executable]
        return "%s < %s" % (executable, self._namelist_path.name)


set_driver_docstring(Orog)
