"""
A driver for UPP.
"""

from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

from iotaa import asset, dryrun, task, tasks

# from uwtools.config.formats.nml import NMLConfig
from uwtools.drivers.driver import Driver
from uwtools.strings import STR
from uwtools.utils.tasks import file, filecopy


class UPP(Driver):
    """
    A driver for UPP.
    """

    def __init__(
        self,
        cycle: datetime,
        leadtime: timedelta,
        config: Optional[Path] = None,
        dry_run: bool = False,
        batch: bool = False,
    ):
        """
        The driver.

        :param cycle: The cycle.
        :param leadtime: The leadtime.
        :param config: Path to config file (read stdin if missing or None).
        :param dry_run: Run in dry-run mode?
        :param batch: Run component via the batch system?
        """
        super().__init__(config=config, dry_run=dry_run, batch=batch, cycle=cycle)
        if self._dry_run:
            dryrun()
        self._cycle = cycle
        self._leadtime = leadtime
        # fcst_time = cycle  # datetime.min() + leadtime
        # valid_time = cycle + leadtime

    # Workflow tasks

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

    # @tasks
    # def files_linked(self):
    #     """
    #     Files linked for run.
    #     """
    #     yield self._taskname("files linked")
    #     yield [
    #         symlink(target=Path(target), linkname=self._rundir / linkname)
    #         for linkname, target in self._driver_config.get("files_to_link", {}).items()
    #     ]

    # @task
    # def namelist_file(self):
    #     """
    #     The namelist file.
    #     """
    #     path = self._rundir / f"itag.{fcst_time.strftime("%H:%M:%S")}"
    #     yield self._taskname(str(path))
    #     yield asset(path, path.is_file)
    #     yield None
    #     path.parent.mkdir(parents=True, exist_ok=True)
    #     self._create_user_updated_config(
    #         config_class=NMLConfig,
    #         config_values=d,
    #         path=path,
    #     )

    @tasks
    def provisioned_run_directory(self):
        """
        Run directory provisioned with all required content.
        """
        yield self._taskname("provisioned run directory")
        yield [
            self.files_copied(),
            # self.files_linked(),
            # self.namelist_file(),
            # self.runscript(),
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

    # Private helper methods

    @property
    def _driver_name(self) -> str:
        """
        Returns the name of this driver.
        """
        return STR.upp

    @task
    def _gribfile(self, infile: Path, link: Path):
        """
        A symlink to an input GRIB file.

        :param link: Link name.
        :param infile: File to link.
        """
        yield self._taskname(str(link))
        yield asset(link, link.is_symlink)
        yield file(path=infile)
        link.parent.mkdir(parents=True, exist_ok=True)
        link.symlink_to(infile)

    def _taskname(self, suffix: str) -> str:
        """
        Returns a common tag for graph-task log messages.

        :param suffix: Log-string suffix.
        """
        return "%s f%03d %s %s" % (
            self._cycle.strftime("%Y%m%d %HZ"),
            self._leadtime,
            self._driver_name,
            suffix,
        )


def _ext(n):
    """
    Maps integers to 3-letter string.
    """
    b = 26
    return "{:A>3}".format(("" if n < b else _ext(n // b)) + chr(65 + n % b))[-3:]
