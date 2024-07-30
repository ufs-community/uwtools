"""
A driver for make_solo_mosaic.
"""

from iotaa import tasks

from uwtools.drivers.driver import DriverTimeInvariant
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
        yield self._taskname("provisioned run directory")
        yield self.runscript()

    # Private helper methods

    @property
    def _driver_name(self) -> str:
        """
        Returns the name of this driver.
        """
        return STR.makesolomosaic

    @property
    def _runcmd(self):
        """
        Returns the full command-line component invocation.
        """
        executable = self._driver_config[STR.execution][STR.executable]
        flags = " ".join(f"--{k} {v}" for k, v in self._driver_config["config"].items())
        return f"{executable} {flags}"

    def _taskname(self, suffix: str) -> str:
        """
        Returns a common tag for graph-task log messages.

        :param suffix: Log-string suffix.
        """
        return "%s %s" % (self._driver_name, suffix)
