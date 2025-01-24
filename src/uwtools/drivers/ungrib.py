"""
A driver for the ungrib component.
"""

from datetime import timedelta
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

    # Workflow tasks

    @tasks
    def gribfiles(self):
        """
        Symlinks to all the GRIB files.
        """
        yield self.taskname("GRIB files")
        gribfiles = self.config["gribfiles"]
        offset = abs(gribfiles["offset"])
        endhour = gribfiles["forecast_length"] + offset
        interval = gribfiles["interval_hours"]
        cycle_hour = int((self._cycle - timedelta(hours=offset)).strftime("%H"))
        links = []
        for n, boundary_hour in enumerate(range(offset, endhour + 1, interval)):
            infile = Path(
                gribfiles["path"].format(cycle_hour=cycle_hour, forecast_hour=boundary_hour)
            )
            link_name = self.rundir / f"GRIBFILE.{_ext(n)}"
            links.append((infile, link_name))
        yield [self._gribfile(infile, link) for infile, link in links]

    @task
    def namelist_file(self):
        """
        The namelist file.
        """
        # Do not use offset here. It's relative to the MPAS fcst to run.
        gribfiles = self.config["gribfiles"]
        endhour = gribfiles["forecast_length"]
        end_date = self._cycle + timedelta(hours=endhour)
        interval = int(gribfiles["interval_hours"]) * 3600  # hour to sec
        d = {
            "update_values": {
                "share": {
                    "end_date": end_date.strftime("%Y-%m-%d_%H:00:00"),
                    "interval_seconds": interval,
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
        path = self.rundir / "namelist.wps"
        yield self.taskname(str(path))
        yield asset(path, path.is_file)
        yield None
        self._create_user_updated_config(
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

    # Private helper methods

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


def _ext(n):
    """
    Return a 3-letter representation of the given integer.

    :param n: The integer to convert to a string representation.
    """
    b = 26
    return "{:A>3}".format(("" if n < b else _ext(n // b)) + chr(65 + n % b))[-3:]


set_driver_docstring(Ungrib)
