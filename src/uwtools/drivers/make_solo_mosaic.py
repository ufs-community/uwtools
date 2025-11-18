"""
A driver for make_solo_mosaic.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from iotaa import collection

from uwtools.drivers.driver import DriverTimeInvariant
from uwtools.drivers.support import set_driver_docstring
from uwtools.strings import STR

if TYPE_CHECKING:
    from pathlib import Path


class MakeSoloMosaic(DriverTimeInvariant):
    """
    A driver for make_solo_mosaic.
    """

    # Workflow tasks

    @collection
    def provisioned_rundir(self):
        """
        Run directory provisioned with all required content.
        """
        yield self.taskname("provisioned run directory")
        yield self.runscript()

    @property
    def output(self) -> dict[str, Path]:
        """
        Returns a description of the file(s) created when this component runs.
        """
        mosaic_name = self.config["config"].get("mosaic_name", "mosaic")
        return {"path": (self.rundir / mosaic_name).with_suffix(".nc")}

    # Public helper methods

    def taskname(self, suffix: str | None = None) -> str:
        """
        Return a common tag for graph-task log messages.

        :param suffix: Log-string suffix.
        """
        return "%s %s" % (self.driver_name(), suffix)

    # Public helper methods

    @classmethod
    def driver_name(cls) -> str:
        """
        The name of this driver.
        """
        return STR.makesolomosaic

    # Private helper methods

    @property
    def _runcmd(self):
        """
        The full command-line component invocation.
        """
        executable = self.config[STR.execution][STR.executable]
        flags = " ".join(f"--{k} {v}" for k, v in self.config["config"].items())
        return f"{executable} {flags}"


set_driver_docstring(MakeSoloMosaic)
