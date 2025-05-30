"""
An assets driver for UPP.
"""

from iotaa import tasks

from uwtools.drivers.driver import AssetsCycleLeadtimeBased
from uwtools.drivers.support import set_driver_docstring
from uwtools.drivers.upp_common import UPPCommon
from uwtools.strings import STR


class UPPAssets(UPPCommon, AssetsCycleLeadtimeBased):
    """
    An assets driver for UPP.
    """

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
        ]

    # Public helper methods

    @classmethod
    def driver_name(cls) -> str:
        """
        The name of this driver.
        """
        return STR.upp_assets


set_driver_docstring(UPPAssets)
