"""
A driver for UPP.
"""

from iotaa import tasks

from uwtools.drivers.driver import DriverCycleLeadtimeBased
from uwtools.drivers.support import set_driver_docstring
from uwtools.drivers.upp_assets import UPPAssets
from uwtools.drivers.upp_common import UPPCommon
from uwtools.strings import STR


class UPP(DriverCycleLeadtimeBased, UPPCommon):
    """
    A driver for UPP.
    """

    files_copied = files_linked = namelist_file = lambda _: ...

    # Workflow tasks

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

    # Private helper methods

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
            "%s < %s" % (execution[STR.executable], self.namelist_path.name),
        ]
        return " ".join(filter(None, components))


set_driver_docstring(UPP)

for k, v in vars(UPPAssets).items():
    if not k.startswith("_") and k not in ["driver_name"]:
        setattr(UPP, k, v)
