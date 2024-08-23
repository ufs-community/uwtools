"""
A driver for the ioda component.
"""

from iotaa import tasks

from uwtools.drivers.jedi_base import JEDIBase
from uwtools.drivers.support import set_driver_docstring
from uwtools.strings import STR


class IODA(JEDIBase):
    """
    A driver for the IODA component.
    """

    # Workflow tasks

    @tasks
    def provisioned_rundir(self):
        """
        Run directory provisioned with all required content.
        """
        yield self.taskname("provisioned run directory")
        yield [
            self.configuration_file(),
            self.files_copied(),
            self.files_linked(),
            self.runscript(),
        ]

    # Public helper methods

    @classmethod
    def driver_name(cls) -> str:
        """
        The name of this driver.
        """
        return STR.ioda

    # Private helper methods

    @property
    def _config_fn(self) -> str:
        """
        The name of the config file used in execution.
        """
        return "ioda.yaml"

    @property
    def _runcmd(self) -> str:
        """
        The full command-line component invocation.
        """
        executable = self.config[STR.execution][STR.executable]
        jedi_config = str(self.rundir / self._config_fn)
        return " ".join([executable, jedi_config])


set_driver_docstring(IODA)
