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
        yield self._taskname("GRIB files")
        gfs_files = self._driver_config["gfs_files"]
        offset = abs(gfs_files["offset"])
        endhour = gfs_files["forecast_length"] + offset
        interval = gfs_files["interval_hours"]
        cycle_hour = int((self._cycle - timedelta(hours=offset)).strftime("%H"))
        links = []
        for n, boundary_hour in enumerate(range(offset, endhour + 1, interval)):
            infile = Path(
                gfs_files["path"].format(cycle_hour=cycle_hour, forecast_hour=boundary_hour)
            )
            link_name = self._rundir / f"GRIBFILE.{_ext(n)}"
            links.append((infile, link_name))
        yield [self._gribfile(infile, link) for infile, link in links]

    @task
    def namelist_file(self):
        """
        The namelist file.
        """
        # Do not use offset here. It's relative to the MPAS fcst to run.
        gfs_files = self._driver_config["gfs_files"]
        endhour = gfs_files["forecast_length"]
        end_date = self._cycle + timedelta(hours=endhour)
        interval = int(gfs_files["interval_hours"]) * 3600  # hour to sec
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
    def provisioned_rundir(self):
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


def _ext(n):
    """
    Maps integers to 3-letter string.
    """
    b = 26
    return "{:A>3}".format(("" if n < b else _ext(n // b)) + chr(65 + n % b))[-3:]


set_driver_docstring(Ungrib)
