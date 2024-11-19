"""
A driver for the MPAS Init component.
"""

from datetime import timedelta
from pathlib import Path

from iotaa import asset, task, tasks

from uwtools.config.formats.nml import NMLConfig
from uwtools.drivers.mpas_base import MPASBase
from uwtools.drivers.support import set_driver_docstring
from uwtools.strings import STR
from uwtools.utils.tasks import file, symlink


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
        yield self.taskname("boundary files")
        lbcs = self.config["boundary_conditions"]
        endhour = lbcs["length"]
        interval = lbcs["interval_hours"]
        symlinks = {}
        boundary_filepath = lbcs["path"]
        for boundary_hour in range(0, endhour + 1, interval):
            file_date = self._cycle + timedelta(hours=boundary_hour)
            fn = f"FILE:{file_date.strftime('%Y-%m-%d_%H')}"
            target = Path(boundary_filepath, fn)
            linkname = self.rundir / fn
            symlinks[target] = linkname
        yield [symlink(target=t, linkname=l) for t, l in symlinks.items()]

    @task
    def namelist_file(self):
        """
        The namelist file.
        """
        fn = "namelist.init_atmosphere"
        yield self.taskname(fn)
        path = self.rundir / fn
        yield asset(path, path.is_file)
        base_file = self.config[STR.namelist].get(STR.basefile)
        yield file(Path(base_file)) if base_file else None
        stop_time = self._cycle + timedelta(hours=self.config["boundary_conditions"]["length"])
        namelist = self.config[STR.namelist]
        update_values = namelist.get(STR.updatevalues, {})
        update_values.setdefault("nhyd_model", {}).update(
            {
                "config_start_time": self._cycle.strftime("%Y-%m-%d_%H:00:00"),
                "config_stop_time": stop_time.strftime("%Y-%m-%d_%H:00:00"),
            }
        )
        namelist[STR.updatevalues] = update_values
        self._create_user_updated_config(
            config_class=NMLConfig,
            config_values=namelist,
            path=path,
            schema=self.namelist_schema(),
        )

    # Public helper methods

    @classmethod
    def driver_name(cls) -> str:
        """
        The name of this driver.
        """
        return STR.mpasinit

    # Private helper methods

    @property
    def _streams_fn(self) -> str:
        """
        The streams filename.
        """
        return "streams.init_atmosphere"


set_driver_docstring(MPASInit)
