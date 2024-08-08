"""
A driver for esg_grid.
"""

from pathlib import Path

from iotaa import asset, task, tasks

from uwtools.config.formats.nml import NMLConfig
from uwtools.drivers.driver import DriverTimeInvariant
from uwtools.drivers.support import set_driver_docstring
from uwtools.strings import STR
from uwtools.utils.tasks import file


class ESGGrid(DriverTimeInvariant):
    """
    A driver for esg_grid.
    """

    # Workflow tasks

    @task
    def namelist_file(self):
        """
        The namelist file.
        """
        fn = "regional_grid.nml"
        yield self.taskname(fn)
        path = self.rundir / fn
        yield asset(path, path.is_file)
        base_file = self.config[STR.namelist].get(STR.basefile)
        yield file(Path(base_file)) if base_file else None
        self._create_user_updated_config(
            config_class=NMLConfig,
            config_values=self.config[STR.namelist],
            path=path,
            schema=self._namelist_schema(schema_keys=["$defs", "namelist_content"]),
        )

    @tasks
    def provisioned_rundir(self):
        """
        Run directory provisioned with all required content.
        """
        yield self.taskname("provisioned run directory")
        yield [
            self.namelist_file(),
            self.runscript(),
        ]

    # Public helper methods

    @property
    def driver_name(self) -> str:
        """
        Returns the name of this driver.
        """
        return STR.esggrid


set_driver_docstring(ESGGrid)
