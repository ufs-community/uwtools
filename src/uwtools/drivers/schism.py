"""
An assets driver for SCHISM.
"""

from pathlib import Path

from iotaa import asset, task, tasks

from uwtools.api.template import render
from uwtools.drivers.driver import AssetsCycleBased
from uwtools.drivers.support import set_driver_docstring
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
        yield self.taskname(fn)
        path = self.rundir / fn
        yield asset(path, path.is_file)
        template_file = Path(self.config[STR.namelist]["template_file"])
        yield file(path=template_file)
        render(
            input_file=template_file,
            output_file=path,
            overrides=self.config[STR.namelist].get("template_values", {}),
        )

    @tasks
    def provisioned_rundir(self):
        """
        Run directory provisioned with all required content.
        """
        yield self.taskname("provisioned run directory")
        yield self.namelist_file()

    # Public helper methods

    @classmethod
    def driver_name(cls) -> str:
        """
        The name of this driver.
        """
        return STR.schism


set_driver_docstring(SCHISM)
