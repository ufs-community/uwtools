"""
A driver for the MPAS Atmosphere component.
"""

from datetime import datetime, timedelta
from pathlib import Path

from iotaa import asset, task, tasks

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

    @tasks
    def boundary_files(self):
        """
        Boundary files.
        """
        yield self.taskname("boundary files")
        lbcs = self.config["lateral_boundary_conditions"]
        endhour = self.config["length"]
        interval = lbcs["interval_hours"]
        symlinks = {}
        for boundary_hour in range(0, endhour + 1, interval):
            file_date = self._cycle + timedelta(hours=boundary_hour)
            fn = f"lbc.{file_date.strftime('%Y-%m-%d_%H.%M.%S')}.nc"
            target = Path(lbcs["path"], fn)
            linkname = self.rundir / fn
            symlinks[target] = linkname
        yield [symlink(target=tgt, linkname=lnk) for tgt, lnk in symlinks.items()]

    @task
    def namelist_file(self):
        """
        The namelist file.
        """
        path = self.rundir / "namelist.atmosphere"
        yield self.taskname(str(path))
        yield asset(path, path.is_file)
        base_file = self.config[STR.namelist].get(STR.basefile)
        yield file(Path(base_file)) if base_file else None
        duration = timedelta(hours=self.config["length"])
        hhmmss = ":".join(
            f"{int(x):02}" for x in str(timedelta(seconds=duration.seconds)).split(":")
        )
        str_duration = "%s%s" % (f"{duration.days:03}_" if duration.days else "", hhmmss)
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
            schema=self.namelist_schema(),
        )

    @tasks
    def provisioned_rundir(self):
        """
        Run directory provisioned with all required content.
        """
        yield self.taskname("provisioned run directory")
        required = [
            self.files_copied(),
            self.files_linked(),
            self.namelist_file(),
            self.runscript(),
            self.streams_file(),
        ]
        if self.config["domain"] == "regional":
            required.append(self.boundary_files())
        yield required

    # Public helper methods

    @classmethod
    def driver_name(cls) -> str:
        """
        The name of this driver.
        """
        return STR.mpas

    # Private helper methods

    @property
    def _initial_and_final_ts(self) -> tuple[datetime, datetime]:
        return self._cycle, self._cycle + timedelta(hours=self.config["length"])

    @property
    def _streams_fn(self) -> str:
        """
        The streams filename.
        """
        return "streams.atmosphere"


set_driver_docstring(MPAS)
