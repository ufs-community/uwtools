"""
A driver for esg_grid.
"""

from pathlib import Path

from iotaa import asset, task, tasks

from uwtools.config.formats.nml import NMLConfig
from uwtools.drivers.driver import Driver
from uwtools.strings import STR
from uwtools.utils.tasks import file


class ESGGrid(Driver):
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
        yield self._taskname(fn)
        path = self._rundir / fn
        yield asset(path, path.is_file)
        base_file = self._driver_config["namelist"].get("base_file")
        yield file(Path(base_file)) if base_file else None
        self._create_user_updated_config(
            config_class=NMLConfig,
            config_values=self._driver_config["namelist"],
            path=path,
            schema=self._namelist_schema(schema_keys=["$defs", "namelist_content"]),
        )

    @tasks
    def provisioned_run_directory(self):
        """
        Run directory provisioned with all required content.
        """
        yield self._taskname("provisioned run directory")
        yield [
            self.namelist_file(),
            self.runscript(),
        ]

    # Private helper methods

    @property
    def _driver_name(self) -> str:
        """
        Returns the name of this driver.
        """
        return STR.esggrid
