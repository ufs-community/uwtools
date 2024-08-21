"""
A driver for shave.
"""

from iotaa import tasks

from uwtools.drivers.driver import DriverTimeInvariant
from uwtools.drivers.support import set_driver_docstring
from uwtools.strings import STR


class Shave(DriverTimeInvariant):
    """
    A driver for shave.
    """

    # Workflow tasks

    @tasks
    def provisioned_rundir(self):
        """
        Run directory provisioned with all required content.
        """
        yield self.taskname("provisioned run directory")
        yield self.runscript()

    # Public helper methods

    @property
    def driver_name(self) -> str:
        """
        Return the name of this driver.
        """
        return STR.shave

    # Private helper methods

    @property
    def _runcmd(self):
        """
        Return the full command-line component invocation.
        """
        executable = self.config[STR.execution][STR.executable]
        config = self.config["config"]
        input_file = config["input_grid_file"]
        output_file = input_file.replace(".nc", "_NH0.nc")
        flags = [config[key] for key in ["nx", "ny", "nh4", "input_grid_file"]]
        flags.append(output_file)
        return f"{executable} {' '.join(str(flag) for flag in flags)}"


set_driver_docstring(Shave)
