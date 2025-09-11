"""
An assets driver for UPP.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from iotaa import task, tasks

from uwtools.drivers import upp_common
from uwtools.drivers.driver import AssetsCycleLeadtimeBased
from uwtools.drivers.support import set_driver_docstring
from uwtools.strings import STR

if TYPE_CHECKING:
    from pathlib import Path


class UPPAssets(AssetsCycleLeadtimeBased):
    """
    An assets driver for UPP.
    """

    # Workflow tasks

    @tasks
    def control_file(self):
        """
        The GRIB control file.
        """
        yield from upp_common.control_file(self)

    @tasks
    def files_copied(self):
        """
        Files copied for run.
        """
        yield from upp_common.files_copied(self)

    @tasks
    def files_linked(self):
        """
        Files linked for run.
        """
        yield from upp_common.files_linked(self)

    @task
    def namelist_file(self):
        """
        The namelist file.
        """
        yield from upp_common.namelist_file(self)

    @tasks
    def provisioned_rundir(self):
        """
        Run directory provisioned with all required content.
        """
        yield self.taskname("provisioned run directory")
        yield [
            self.control_file(),
            self.files_copied(),
            self.files_hardlinked(),
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

    @property
    def output(self) -> dict[str, Path] | dict[str, list[Path]]:
        return upp_common.output(self)


set_driver_docstring(UPPAssets)
