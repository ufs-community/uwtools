"""
A driver for make_hgrid.
"""

from iotaa import tasks

from uwtools.drivers.driver import DriverTimeInvariant
from uwtools.drivers.support import set_driver_docstring
from uwtools.strings import STR


class MakeHgrid(DriverTimeInvariant):
    """
    A driver for make_hgrid.
    """

    # Workflow tasks

    @tasks
    def provisioned_rundir(self):
        """
        Run directory provisioned with all required content.
        """
        yield self.taskname("provisioned run directory")
        yield self.runscript()

    # Private helper methods

    @property
    def _driver_name(self) -> str:
        """
        Returns the name of this driver.
        """
        return STR.makehgrid

    @property
    def _runcmd(self):
        """
        Returns the full command-line component invocation.
        """
        executable = self.config[STR.execution][STR.executable]
        config = self.config["config"]
        flags = []
        for k, v in config.items():
            if isinstance(v, bool):
                flags.append("--%s" % k)
            elif isinstance(v, list):
                flags.append("--%s %s" % (k, ",".join(map(str, v))))
            else:
                flags.append("--%s %s" % (k, v))
        return f"{executable} " + " ".join(flags)


set_driver_docstring(MakeHgrid)
