"""
A driver for UPP.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from iotaa import task, tasks

from uwtools.drivers import upp_common
from uwtools.drivers.driver import DriverCycleLeadtimeBased
from uwtools.drivers.stager import FileStager
from uwtools.drivers.support import set_driver_docstring
from uwtools.strings import STR

if TYPE_CHECKING:
    from pathlib import Path


class UPP(DriverCycleLeadtimeBased, FileStager):
    """
    A driver for UPP.
    """

    # Workflow tasks

    @tasks
    def control_file(self):
        """
        The GRIB control file.
        """
        yield from upp_common.control_file(self)

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
            self.runscript(),
        ]

    # Public helper methods

    @classmethod
    def driver_name(cls) -> str:
        """
        The name of this driver.
        """
        return STR.upp

    @property
    def output(self) -> dict[str, Path] | dict[str, list[Path]]:
        return upp_common.output(self)

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
            "%s < %s" % (execution[STR.executable], upp_common.namelist_path(self).name),
        ]
        return " ".join(filter(None, components))


set_driver_docstring(UPP)
