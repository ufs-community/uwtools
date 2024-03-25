"""
A driver for the ungrib component.
"""

from datetime import datetime, timedelta
from pathlib import Path
from string import ascii_uppercase
from typing import Optional, Tuple

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

    @tasks
    def gribfiles(self):
        """
        Symlinks to all the GRIB files.
        """
        yield self._taskname("gribfiles")
        gfs_files = self._driver_config["gfs_files"]
        offset = abs(gfs_files["offset"])
        endhour = gfs_files["forecast_length"] + offset + 1
        interval = gfs_files["interval_hours"]
        cycle_hour = int((self._cycle - timedelta(hours=offset)).strftime("%H"))
        suffix = "AAA"
        links = []
        for boundary_hour in range(offset, endhour, interval):
            infile = Path(
                gfs_files["path"].format(cycle_hour=cycle_hour, forecast_hour=boundary_hour)
            )
            link_name = self._rundir / f"GRIBFILE.{suffix}"
            links.append((link_name, infile))
            suffix = incr_str(suffix)
        yield [self._gribfile(link, infile) for link, infile in links]

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
            self.gribfiles(),
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
        A symlink to the Vtable file.
        """
        path = self._rundir / "Vtable"
        yield self._taskname(str(path))
        yield asset(path, path.is_symlink)
        infile = Path(self._driver_config["vtable"])
        yield file(path=infile)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.symlink_to(Path(self._driver_config["vtable"]))

    # Private helper methods

    @property
    def _driver_name(self) -> str:
        """
        Returns the name of this driver.
        """
        return STR.ungrib

    @task
    def _gribfile(self, link, infile):
        """
        A symlink to the input GRIB file.

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
        return "%s ungrib %s" % (self._cycle.strftime("%Y%m%d %HZ"), suffix)


def incr_str(s: str) -> str:
    """
    Increment an uppercase string.
    """

    def incr_char(c: str) -> Tuple[int, str]:
        letters = ascii_uppercase
        assert c in letters
        if c == "Z":
            return 1, "A"
        return 0, chr(ord(c) + 1)

    chars = list(s)
    res = []
    while chars:
        carry, next_ = incr_char(chars.pop())
        res.append(next_)
        if not carry:
            break
        if not chars:
            res.append("A")
    res += chars[::-1]
    return "".join(res[::-1])
