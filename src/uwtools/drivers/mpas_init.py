"""
A driver for the mpas-init component.
"""

from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict

from iotaa import asset, dryrun, task, tasks

from uwtools.api.template import render
from uwtools.config.formats.nml import NMLConfig
from uwtools.config.formats.yaml import YAMLConfig
from uwtools.drivers.driver import Driver
from uwtools.strings import STR
from uwtools.utils.tasks import file, filecopy, symlink


class MPASInit(Driver):
    """
    A driver for mpas-init.
    """

    def __init__(self, config: Path, cycle: datetime, dry_run: bool = False, batch: bool = False):
        """
        The driver.

        :param config_file: Path to config file (read stdin if missing or None).
        :param cycle: The cycle.
        :param dry_run: Run in dry-run mode?
        :param batch: Run component via the batch system?
        """
        super().__init__(config=config, dry_run=dry_run, batch=batch, cycle=cycle)
        if self._dry_run:
            dryrun()
        self._cycle = cycle

    # Workflow tasks

    @tasks
    def boundary_files(self):
        """
        Boundary-condition files.
        """
        yield self._taskname("boundary files")
        lbcs = self._driver_config["boundary_conditions"]
        endhour = lbcs["length"]
        interval = lbcs["interval_hours"]
        symlinks = {}
        boundary_filepath = lbcs["path"]
        for boundary_hour in range(0, endhour + 1, interval):
            file_date = self._cycle + timedelta(hours=boundary_hour)
            target = Path(boundary_filepath) / f"FILE:{file_date.strftime('%Y-%m-%d_%H')}"
            linkname = self._rundir / f"FILE:{file_date.strftime('%Y-%m-%d_%H')}"
            symlinks[target] = linkname
        yield [symlink(target=t, linkname=l) for t, l in symlinks.items()]

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
        yield self._taskname("files linked")
        yield [
            symlink(target=Path(target), linkname=self._rundir / linkname)
            for linkname, target in self._driver_config.get("files_to_link", {}).items()
        ]

    @task
    def namelist_file(self):
        """
        The namelist file.
        """
        fn = "namelist.init_atmosphere"
        yield self._taskname(fn)
        path = self._rundir / fn
        yield asset(path, path.is_file)
        yield None
        stop_time = self._cycle + timedelta(
            hours=self._driver_config["boundary_conditions"]["length"]
        )
        d = {
            "nhyd_model": {
                "config_start_time": self._cycle.strftime("%Y-%m-%d_%H:00:00"),
                "config_stop_time": stop_time.strftime("%Y-%m-%d_%H:00:00"),
            }
        }
        namelist = self._driver_config.get("namelist", {})
        values = YAMLConfig(d)
        values.update_values(namelist.get("update_values", {}))
        namelist["update_values"] = values.data
        self._create_user_updated_config(
            config_class=NMLConfig,
            config_values=namelist,
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
            self.namelist_file(),
            self.runscript(),
            self.streams_file(),
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
    def streams_file(self):
        """
        The streams file.
        """
        fn = "streams.init_atmosphere"
        yield self._taskname(fn)
        path = self._rundir / fn
        yield asset(path, path.is_file)
        yield file(path=Path(self._driver_config["streams"]["path"]))
        render(
            input_file=Path(self._driver_config["streams"]["path"]),
            output_file=path,
            values_src=self._driver_config["streams"]["values"],
        )

    # Private helper methods

    @property
    def _driver_name(self) -> str:
        """
        Returns the name of this driver.
        """
        return STR.mpasinit

    @property
    def _resources(self) -> Dict[str, Any]:
        """
        Returns configuration data for the runscript.
        """
        return {
            "account": self._config["platform"]["account"],
            "rundir": self._rundir,
            "scheduler": self._config["platform"]["scheduler"],
            **self._driver_config.get("execution", {}).get("batchargs", {}),
        }

    def _taskname(self, suffix: str) -> str:
        """
        Returns a common tag for graph-task log messages.

        :param suffix: Log-string suffix.
        """
        return "%s %s %s" % (self._cycle.strftime("%Y%m%d %HZ"), self._driver_name, suffix)
        # return "%s mpas-init %s" % (self._cycle.strftime("%Y%m%d %HZ"), suffix)
