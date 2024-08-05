"""
A driver for the MPAS Atmosphere component.
"""

from datetime import timedelta
from pathlib import Path

from iotaa import asset, task

from uwtools.config.formats.nml import NMLConfig
from uwtools.drivers.mpas_base import MPASBase
from uwtools.drivers.support import set_driver_docstring
from uwtools.strings import STR
from uwtools.utils.tasks import file, symlink


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
        lbcs = self.config["lateral_boundary_conditions"]
        endhour = self.config["length"]
        interval = lbcs["interval_hours"]
        symlinks = {}
        for boundary_hour in range(0, endhour + 1, interval):
            file_date = self._cycle + timedelta(hours=boundary_hour)
            fn = f"lbc.{file_date.strftime('%Y-%m-%d_%H.%M.%S')}.nc"
            linkname = self.rundir / fn
            symlinks[linkname] = Path(lbcs["path"], fn)
        yield [symlink(target=t, linkname=l) for l, t in symlinks.items()]

    @task
    def namelist_file(self):
        """
        The namelist file.
        """
        path = self.rundir / "namelist.atmosphere"
        yield self._taskname(str(path))
        yield asset(path, path.is_file)
        base_file = self.config[STR.namelist].get(STR.basefile)
        yield file(Path(base_file)) if base_file else None
        duration = timedelta(hours=self.config["length"])
        str_duration = str(duration).replace(" days, ", "_")
        namelist = self.config[STR.namelist]
        update_values = namelist.get(STR.updatevalues, {})
        update_values.setdefault("nhyd_model", {}).update(
            {
                "config_start_time": self._cycle.strftime("%Y-%m-%d_%H:00:00"),
                "config_run_duration": str_duration,
            }
        )
        namelist[STR.updatevalues] = update_values
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


set_driver_docstring(MPAS)
