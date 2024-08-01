"""
A driver for the MPAS Atmosphere component.
"""

from datetime import timedelta
from pathlib import Path

from iotaa import asset, task

from uwtools.config.formats.nml import NMLConfig
from uwtools.drivers.mpas_base import MPASBase
from uwtools.exceptions import UWConfigError
from uwtools.strings import STR
from uwtools.utils.tasks import symlink


class MPAS(MPASBase):
    """
    A driver for MPAS Atmosphere.
    """

    # Workflow tasks

    @task
    def boundary_files(self):
        """
        Boundary files.
        """
        yield self._taskname("boundary files")
        lbcs = self._driver_config["lateral_boundary_conditions"]
        endhour = self._driver_config["length"]
        interval = lbcs["interval_hours"]
        symlinks = {}
        for boundary_hour in range(0, endhour + 1, interval):
            file_date = self._cycle + timedelta(hours=boundary_hour)
            fn = f"lbc.{file_date.strftime('%Y-%m-%d_%H.%M.%S')}.nc"
            linkname = self._rundir / fn
            symlinks[linkname] = Path(lbcs["path"]) / fn
        yield [symlink(target=t, linkname=l) for l, t in symlinks.items()]

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
        str_duration = str(duration).replace(" days, ", "_")
        try:
            namelist = self._driver_config["namelist"]
        except KeyError as e:
            raise UWConfigError(
                "Provide either a 'namelist' YAML block or the %s file" % path
            ) from e
        update_values = namelist.get("update_values", {})
        update_values.setdefault("nhyd_model", {}).update(
            {
                "config_start_time": self._cycle.strftime("%Y-%m-%d_%H:00:00"),
                "config_run_duration": str_duration,
            }
        )
        namelist["update_values"] = update_values
        self._create_user_updated_config(
            config_class=NMLConfig,
            config_values=namelist,
            path=path,
            schema=self._namelist_schema(),
        )

    # Private helper methods

    @property
    def _driver_name(self) -> str:
        """
        Returns the name of this driver.
        """
        return STR.mpas

    @property
    def _streams_fn(self) -> str:
        """
        The streams filename.
        """
        return "streams.atmosphere"
