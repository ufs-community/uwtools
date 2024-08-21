"""
An assets driver for ww3.
"""

from pathlib import Path

from iotaa import asset, task, tasks

from uwtools.api.template import render
from uwtools.drivers.driver import AssetsCycleBased
from uwtools.drivers.support import set_driver_docstring
from uwtools.strings import STR
from uwtools.utils.tasks import file


class WaveWatchIII(AssetsCycleBased):
    """
    An assets driver for ww3.
    """

    # Workflow tasks

    @task
    def namelist_file(self):
        """
        Render the namelist from the template file.
        """
        fn = "ww3_shel.nml"
        yield self.taskname(fn)
        path = self.rundir / fn
        yield asset(path, path.is_file)
        template_file = Path(self.config[STR.namelist]["template_file"])
        yield file(template_file)
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
        yield [
            self.namelist_file(),
            self.restart_directory(),
        ]

    @task
    def restart_directory(self):
        """
        The restart directory.
        """
        yield self.taskname("restart directory")
        path = self.rundir / "restart_wave"
        yield asset(path, path.is_dir)
        yield None
        path.mkdir(parents=True)

    # Public helper methods

    @property
    def driver_name(self) -> str:
        """
        The name of this driver.
        """
        return STR.ww3


set_driver_docstring(WaveWatchIII)
