"""
A driver for the MPAS component.
"""

from datetime import datetime
from pathlib import Path
from typing import Optional

from iotaa import asset, dryrun, task, tasks

from uwtools.config.formats.nml import NMLConfig
from uwtools.drivers.driver import Driver
from uwtools.strings import STR
from uwtools.utils.tasks import file


class MPAS(Driver):
    """
    A driver for MPAS.
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

        :param cycle: The cycle.
        :param config: Path to config file (read stdin if missing or None).
        :param dry_run: Run in dry-run mode?
        :param batch: Run component via the batch system?
        """
        super().__init__(config=config, dry_run=dry_run, batch=batch, cycle=cycle)
        if self._dry_run:
            dryrun()
        self._cycle = cycle

    # Workflow tasks

    @task
    def boundary_files(self):
        """
        Boundary condition files.
        """
        yield self._taskname("boundary files")
        lbcs = self._driver_config["lateral_boundary_conditions"]
        endhour = self._driver_config["length"]
        interval = lbcs["interval_hours"]
        symlinks = {}
        for boundary_hour in range(0, endhour, interval):
            file_date = self._cycle + timedelta(hours=boundary_hour)
            fn = file_date.strftime(lbcs["filename"])
            linkname = self._rundir / fn
            symlinks[linkname] = Path(lbcs["path"]) / fn
        yield [
            symlink(target=t, linkname=l)
            for t, l in symlinks.items()
        ]

    @tasks
    def files_copied(self):
        """
        Files copied for run.
        """
        yield self._taskname("files copied")
        yield [
            filecopy(src=Path(src), dst=self._rundir / dst)
            for dst, src in self._driver_config.get("files_to_copy", {}).items()
        ]

    @tasks
    def files_linked(self):
        """
        Files linked for run.
        """
        pass

    @task
    def namelist_file(self):
        """
        The namelist file.
        """
        path = self._rundir / "namelist.atmosphere"
        yield self._taskname(str(path))
        yield asset(path, path.is_file)
        yield None
        duration = timedelta(hours=self._driver_config["length"])
        duration = str(duration).replace(" days, ", "")
        d = {
            "nhyd_model": {
                "config_start_time": self._cycle.strftime("%Y-%m-%d_%H:00:00"),
                "config_run_duration": duration,
            }
        }
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
            self.boundary_files(),
            self.files_copied(),
            self.files_linked(),
            self.namelist(),
            self.runscript(),
            self.streams(),
        ]

    @task
    def streams(self):
        """
        The streams file.
        """
        fn = "streams.atmosphere"
        yield self._taskname(fn)
        path = self._rundir / fn
        yield asset(path, path.is_file)
        yield self._driver_config["streams"]["path"]
        render(
            input_file=self._driver_config["streams"]["path"],
            output_file=path,
            values_src=self._driver_config["streams"]["values"],
        )

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

    # Private helper methods

    @property
    def _driver_name(self) -> str:
        """
        Returns the name of this driver.
        """
        return STR.mpas

    def _taskname(self, suffix: str) -> str:
        """
        Returns a common tag for graph-task log messages.

        :param suffix: Log-string suffix.
        """
        return "%s %s %s" % (self._cycle.strftime("%Y%m%d %HZ"), self._driver_name, suffix)
