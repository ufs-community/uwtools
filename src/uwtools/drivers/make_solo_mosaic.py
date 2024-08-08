"""
A driver for make_solo_mosaic.
"""

from iotaa import tasks

from uwtools.drivers.driver import DriverTimeInvariant
from uwtools.drivers.support import set_driver_docstring
from uwtools.strings import STR


class MakeSoloMosaic(DriverTimeInvariant):
    """
    A driver for make_solo_mosaic.
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

    def taskname(self, suffix: str) -> str:
        """
        Returns a common tag for graph-task log messages.

        :param suffix: Log-string suffix.
        """
        return "%s %s" % (self.driver_name, suffix)

    # Public helper methods

    @property
    def driver_name(self) -> str:
        """
        Returns the name of this driver.
        """
        return STR.makesolomosaic

    # Private helper methods

    @property
    def _runcmd(self):
        """
        Returns the full command-line component invocation.
        """
        executable = self.config[STR.execution][STR.executable]
        flags = " ".join(f"--{k} {v}" for k, v in self.config["config"].items())
        return f"{executable} {flags}"


set_driver_docstring(MakeSoloMosaic)
