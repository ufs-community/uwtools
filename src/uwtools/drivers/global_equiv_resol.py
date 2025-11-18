"""
A driver for the global_equiv_resol component.
"""

from pathlib import Path

from iotaa import Asset, collection, external

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
        path = Path(self.config["input_grid_file"])
        yield self.taskname(path.name)
        yield Asset(path, path.is_file)

    @collection
    def provisioned_rundir(self):
        """
        Run directory provisioned with all required content.
        """
        yield self.taskname("provisioned run directory")
        yield [
            self.input_file(),
            self.runscript(),
        ]

    # Public helper methods

    @classmethod
    def driver_name(cls) -> str:
        """
        The name of this driver.
        """
        return STR.globalequivresol

    @property
    def output(self) -> dict[str, Path]:
        """
        Returns a description of the file(s) created when this component runs.
        """
        return {"path": Path(self.config["input_grid_file"])}

    # Private helper methods

    @property
    def _runcmd(self):
        """
        The full command-line component invocation.
        """
        executable = self.config[STR.execution][STR.executable]
        input_file_path = self.config["input_grid_file"]
        return f"{executable} {input_file_path}"


set_driver_docstring(GlobalEquivResol)
