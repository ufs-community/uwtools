"""
An assets driver for SCHISM.
"""

from pathlib import Path

from iotaa import asset, task, tasks

from uwtools.api.template import render
from uwtools.drivers.driver import AssetsCycleBased
from uwtools.strings import STR
from uwtools.utils.tasks import file


class SCHISM(AssetsCycleBased):
    """
    An assets driver for SCHISM.
    """

    # Workflow tasks

    @task
    def namelist_file(self):
        """
        Render the namelist from the template file.
        """
        fn = "param.nml"
        yield self._taskname(fn)
        path = self._rundir / fn
        yield asset(path, path.is_file)
        template_file = Path(self._driver_config[STR.namelist]["template_file"])
        yield file(path=template_file)
        render(
            input_file=template_file,
            output_file=path,
            overrides=self._driver_config[STR.namelist]["template_values"],
        )

    @tasks
    def provisioned_rundir(self):
        """
        Run directory provisioned with all required content.
        """
        yield self._taskname("provisioned run directory")
        yield self.namelist_file()

    # Private helper methods

    @property
    def _driver_name(self) -> str:
        """
        Returns the name of this driver.
        """
        return STR.schism
