"""
A driver for the ungrib component.
"""

from datetime import datetime, timedelta
from pathlib import Path

from iotaa import asset, task, tasks

from uwtools.config.formats.nml import NMLConfig
from uwtools.drivers.driver import DriverCycleBased
from uwtools.drivers.support import set_driver_docstring
from uwtools.strings import STR
from uwtools.utils.tasks import file


class Ungrib(DriverCycleBased):
    """
    A driver for ungrib.
    """

    PREFIX = "FILE"
    TIMEFMT = "%Y-%m-%d_%H:00:00"

    # Workflow tasks

    @tasks
    def gribfiles(self):
        """
        Symlinks to all the GRIB files.
        """
        yield self.taskname("GRIB files")
        files = [Path(p) for p in self.config["gribfiles"]["files"]]
        yield [
            self._gribfile(src, self.rundir / f"GRIBFILE.{_ext(i)}") for i, src in enumerate(files)
        ]

    @task
    def namelist_file(self):
        """
        The namelist file.
        """
        d = {
            "update_values": {
                "share": {
                    "end_date": self._end_date.strftime(self.TIMEFMT),
                    "interval_seconds": self._interval,
                    "max_dom": 1,
                    "start_date": self._cycle.strftime(self.TIMEFMT),
                    "wrf_core": "ARW",
                },
                "ungrib": {
                    "out_format": "WPS",
                    "prefix": self.PREFIX,
                },
            }
        }
        path = self.rundir / "namelist.wps"
        yield self.taskname(str(path))
        yield asset(path, path.is_file)
        yield None
        self.create_user_updated_config(
            config_class=NMLConfig,
            config_values=d,
            path=path,
        )

    @tasks
    def provisioned_rundir(self):
        """
        Run directory provisioned with all required content.
        """
        yield self.taskname("provisioned run directory")
        yield [
            self.gribfiles(),
            self.namelist_file(),
            self.runscript(),
            self.vtable(),
        ]

    @task
    def vtable(self):
        """
        A symlink to the Vtable file.
        """
        path = self.rundir / "Vtable"
        yield self.taskname(str(path))
        yield asset(path, path.is_symlink)
        infile = Path(self.config["vtable"])
        yield file(path=infile)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.symlink_to(Path(self.config["vtable"]))

    # Public helper methods

    @classmethod
    def driver_name(cls) -> str:
        """
        The name of this driver.
        """
        return STR.ungrib

    @property
    def output(self) -> dict[str, list[Path]]:
        """
        Returns a description of the file(s) created when this component runs.
        """
        paths = []
        ts = self._cycle
        while ts <= self._end_date:
            fn = "%s:%s" % (self.PREFIX, ts.strftime(self.TIMEFMT))
            paths.append(self.rundir / fn)
            ts += timedelta(seconds=self._interval)
        return {"paths": paths}

    # Private helper methods

    @property
    def _end_date(self) -> datetime:
        endhour = self.config["gribfiles"]["max_leadtime"]
        return self._cycle + timedelta(hours=endhour)

    @task
    def _gribfile(self, infile: Path, link: Path):
        """
        A symlink to an input GRIB file.

        :param link: Link name.
        :param infile: File to link.
        """
        yield self.taskname(str(link))
        yield asset(link, link.is_symlink)
        yield file(path=infile)
        link.parent.mkdir(parents=True, exist_ok=True)
        link.symlink_to(infile)

    @property
    def _interval(self) -> int:
        return int(self.config["gribfiles"]["interval_hours"]) * 3600


def _ext(n: int) -> str:
    """
    Return a 3-letter representation of the given integer.

    :param n: The integer to convert to a string representation.
    """
    b = 26
    return "{:A>3}".format(("" if n < b else _ext(n // b)) + chr(65 + n % b))[-3:]


set_driver_docstring(Ungrib)
