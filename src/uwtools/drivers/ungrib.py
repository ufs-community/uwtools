"""
A driver for the ungrib component.
"""

from datetime import datetime
from pathlib import Path
from typing import Optional

from iotaa import asset, dryrun, task, tasks

from uwtools.config.formats.nml import NMLConfig
from uwtools.drivers.driver import Driver
from uwtools.strings import STR
from uwtools.utils.tasks import file


class Ungrib(Driver):
    """
    A driver for ungrib.
    """

    def __init__(
        self,
        cycle: datetime,
        config: Optional[Path] = None,
        dry_run: bool = False,
        batch: bool = False,
    ):
        """
        The driver.

        :param cycle: The forecast cycle.
        :param config: Path to config file (read stdin if missing or None).
        :param dry_run: Run in dry-run mode?
        :param batch: Run component via the batch system?
        """
        super().__init__(config=config, dry_run=dry_run, batch=batch)
        self._config.dereference(context={"cycle": cycle})
        if self._dry_run:
            dryrun()
        self._cycle = cycle

    # Workflow tasks

    @task
    def gribfile_aaa(self):
        """
        The gribfile.
        """
        path = self._rundir / "GRIBFILE.AAA"
        yield self._taskname(str(path))
        yield asset(path, path.is_symlink)
        infile = Path(self._driver_config["gfs_file"])
        yield file(path=infile)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.symlink_to(infile)

    @task
    def namelist_file(self):
        """
        The namelist file.
        """
        d = {
            "update_values": {
                "share": {
                    "end_date": self._cycle.strftime("%Y-%m-%d_%H:00:00"),
                    "interval_seconds": 1,
                    "max_dom": 1,
                    "start_date": self._cycle.strftime("%Y-%m-%d_%H:00:00"),
                    "wrf_core": "ARW",
                },
                "ungrib": {
                    "out_format": "WPS",
                    "prefix": "FILE",
                },
            }
        }
        path = self._rundir / "namelist.wps"
        yield self._taskname(str(path))
        yield asset(path, path.is_file)
        yield None
        path.parent.mkdir(parents=True, exist_ok=True)
        self._create_user_updated_config(
            config_class=NMLConfig,
            config_values=d,
            path=path,
        )

    @tasks
    def provisioned_run_directory(self):
        """
        Run directory provisioned with all required content.
        """
        yield self._taskname("provisioned run directory")
        yield [
            self.gribfile_aaa(),
            self.namelist_file(),
            self.runscript(),
            self.vtable(),
        ]

    @task
    def runscript(self):
        """
        The runscript.
        """
        path = self._runscript_path
        yield self._taskname(path.name)
        yield asset(path, path.is_file)
        yield None
        self._write_runscript(path=path, envvars={})

    @task
    def vtable(self):
        """
        The Vtable.
        """
        path = self._rundir / "Vtable"
        yield self._taskname(str(path))
        yield asset(path, path.is_symlink)
        yield None
        path.parent.mkdir(parents=True, exist_ok=True)
        path.symlink_to(Path(self._driver_config["vtable"]))

    # Private helper methods

    @property
    def _driver_name(self) -> str:
        """
        Returns the name of this driver.
        """
        return STR.ungrib

    def _taskname(self, suffix: str) -> str:
        """
        Returns a common tag for graph-task log messages.

        :param suffix: Log-string suffix.
        """
        return "%s ungrib %s" % (self._cycle.strftime("%Y%m%d %HZ"), suffix)
