"""
A driver for the global_equiv_resol component.
"""

from pathlib import Path

from iotaa import asset, external, tasks

from uwtools.drivers.driver import DriverTimeInvariant
from uwtools.drivers.support import set_driver_docstring
from uwtools.strings import STR


class GlobalEquivResol(DriverTimeInvariant):
    """
    A driver for global_equiv_resol.
    """

    # Workflow tasks

    @external
    def input_file(self):
        """
        Ensure the specified input grid file exists.
        """
        path = Path(self._driver_config["input_grid_file"])
        yield self._taskname(path.name)
        yield asset(path, path.is_file)

    @tasks
    def provisioned_rundir(self):
        """
        Run directory provisioned with all required content.
        """
        yield self._taskname("provisioned run directory")
        yield [
            self.input_file(),
            self.runscript(),
        ]

    # Private helper methods

    @property
    def _driver_name(self) -> str:
        """
        Returns the name of this driver.
        """
        return STR.globalequivresol

    @property
    def _runcmd(self):
        """
        Returns the full command-line component invocation.
        """
        executable = self._driver_config[STR.execution][STR.executable]
        input_file_path = self._driver_config["input_grid_file"]
        return f"{executable} {input_file_path}"


set_driver_docstring(GlobalEquivResol)
