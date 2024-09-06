"""
A driver for orog_gsl.
"""

from pathlib import Path

from iotaa import asset, task, tasks

from uwtools.drivers.driver import DriverTimeInvariant
from uwtools.drivers.support import set_driver_docstring
from uwtools.strings import STR
from uwtools.utils.file import writable
from uwtools.utils.tasks import symlink


class OrogGSL(DriverTimeInvariant):
    """
    A driver for orog_gsl.
    """

    # Workflow tasks

    @task
    def input_config_file(self):
        """
        The input config file.
        """
        path = self._input_config_path
        yield self.taskname(str(path))
        yield asset(path, path.is_file)
        yield None
        inputs = [str(self.config["config"][k]) for k in ("tile", "resolution", "halo")]
        with writable(path) as f:
            print("\n".join(inputs), file=f)

    @task
    def input_grid_file(self):
        """
        The input grid file.
        """
        fn = "C%s_grid.tile%s.halo%s.nc" % tuple(
            self.config["config"][k] for k in ["resolution", "tile", "halo"]
        )
        src = Path(self.config["config"]["input_grid_file"])
        dst = self.rundir / fn
        yield self.taskname("Input grid")
        yield asset(dst, dst.is_file)
        yield symlink(target=src, linkname=dst)

    @tasks
    def provisioned_rundir(self):
        """
        Run directory provisioned with all required content.
        """
        yield self.taskname("provisioned run directory")
        yield [
            self.input_config_file(),
            self.input_grid_file(),
            self.runscript(),
            self.topo_data_2p5m(),
            self.topo_data_30s(),
        ]

    @task
    def topo_data_2p5m(self):
        """
        Global topographic data on 2.5-minute lat-lon grid.
        """
        fn = "geo_em.d01.lat-lon.2.5m.HGT_M.nc"
        src = Path(self.config["config"]["topo_data_2p5m"])
        dst = self.rundir / fn
        yield self.taskname("Input grid")
        yield asset(dst, dst.is_file)
        yield symlink(target=src, linkname=dst)

    @task
    def topo_data_30s(self):
        """
        Global topographic data on 30-second lat-lon grid.
        """
        fn = "HGT.Beljaars_filtered.lat-lon.30s_res.nc"
        src = Path(self.config["config"]["topo_data_30s"])
        dst = self.rundir / fn
        yield self.taskname("Input grid")
        yield asset(dst, dst.is_file)
        yield symlink(target=src, linkname=dst)

    # Public helper methods

    @classmethod
    def driver_name(cls) -> str:
        """
        The name of this driver.
        """
        return STR.oroggsl

    # Private helper methods
    @property
    def _input_config_path(self) -> Path:
        """
        Path to the input config file.
        """
        return self.rundir / "orog_gsl.cfg"

    @property
    def _runcmd(self):
        """
        The full command-line component invocation.
        """
        executable = self.config[STR.execution][STR.executable]
        return "'%s' < %s" % (executable, self._input_config_path.name)


set_driver_docstring(OrogGSL)
