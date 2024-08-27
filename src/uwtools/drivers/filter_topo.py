"""
A driver for filter_topo.
"""

from pathlib import Path

from iotaa import asset, task, tasks

from uwtools.config.formats.nml import NMLConfig
from uwtools.drivers.driver import DriverTimeInvariant
from uwtools.drivers.support import set_driver_docstring
from uwtools.strings import STR
from uwtools.utils.tasks import symlink


class FilterTopo(DriverTimeInvariant):
    """
    A driver for filter_topo.
    """

    # Workflow tasks

    @task
    def input_grid_file(self):
        """
        The input grid file.
        """
        src = Path(self.config["config"]["input_grid_file"])
        dst = Path(self.config[STR.rundir], src.name)
        yield self.taskname("Input grid")
        yield asset(dst, dst.is_file)
        yield symlink(target=src, linkname=dst)

    @task
    def namelist_file(self):
        """
        The namelist file.
        """
        fn = "input.nml"
        path = self.rundir / fn
        yield self.taskname(f"namelist file {fn}")
        yield asset(path, path.is_file)
        yield None
        self._create_user_updated_config(
            config_class=NMLConfig,
            config_values=self.config[STR.namelist],
            path=path,
            schema=self.namelist_schema(),
        )

    @tasks
    def provisioned_rundir(self):
        """
        Run directory provisioned with all required content.
        """
        yield self.taskname("provisioned run directory")
        yield [
            self.input_grid_file(),
            self.namelist_file(),
            self.runscript(),
        ]

    # Public helper methods

    @classmethod
    def driver_name(cls) -> str:
        """
        The name of this driver.
        """
        return STR.filtertopo


set_driver_docstring(FilterTopo)
