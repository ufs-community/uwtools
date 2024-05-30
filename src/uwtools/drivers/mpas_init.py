"""
A driver for the MPAS Init component.
"""

from datetime import timedelta
from pathlib import Path

from iotaa import asset, task, tasks

from uwtools.config.formats.nml import NMLConfig
from uwtools.drivers.mpas_base import MPASBase
from uwtools.exceptions import UWConfigError
from uwtools.strings import STR
from uwtools.utils.tasks import symlink


class MPASInit(MPASBase):
    """
    A driver for MPAS Init.
    """

    # Workflow tasks

    @tasks
    def boundary_files(self):
        """
        Boundary files.
        """
        yield self._taskname("boundary files")
        lbcs = self._driver_config["boundary_conditions"]
        endhour = lbcs["length"]
        interval = lbcs["interval_hours"]
        symlinks = {}
        boundary_filepath = lbcs["path"]
        for boundary_hour in range(0, endhour + 1, interval):
            file_date = self._cycle + timedelta(hours=boundary_hour)
            fn = f"FILE:{file_date.strftime('%Y-%m-%d_%H')}"
            target = Path(boundary_filepath) / fn
            linkname = self._rundir / fn
            symlinks[target] = linkname
        yield [symlink(target=t, linkname=l) for t, l in symlinks.items()]

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
                "config_stop_time": stop_time.strftime("%Y-%m-%d_%H:00:00"),
            }
        )
        namelist["update_values"] = update_values
        self._create_user_updated_config(
            config_class=NMLConfig,
            config_values=namelist,
            path=path,
        )

    # Private helper methods

    @property
    def _driver_name(self) -> str:
        """
        Returns the name of this driver.
        """
        return STR.mpasinit

    @property
    def _streams_fn(self) -> str:
        """
        Teh streams filename.
        """
        return "streams.init_atmosphere"
