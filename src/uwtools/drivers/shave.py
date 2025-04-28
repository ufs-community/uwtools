"""
A driver for shave.
"""

from pathlib import Path

from iotaa import asset, task, tasks

from uwtools.drivers.driver import DriverTimeInvariant
from uwtools.drivers.support import set_driver_docstring
from uwtools.strings import STR
from uwtools.utils.file import writable
from uwtools.utils.tasks import file


class Shave(DriverTimeInvariant):
    """
    A driver for shave.
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
        config = self.config["config"]
        input_file = Path(config["input_grid_file"])
        yield file(path=input_file)
        flags = [
            config[key] for key in ["nx", "ny", "nhalo", "input_grid_file", "output_grid_file"]
        ]
        content = "{} {} {} '{}' '{}'".format(*flags)
        with writable(path) as f:
            print(content, file=f)

    @tasks
    def provisioned_rundir(self):
        """
        Run directory provisioned with all required content.
        """
        yield self.taskname("provisioned run directory")
        yield [
            self.input_config_file(),
            self.runscript(),
        ]

    # Public helper methods

    @classmethod
    def driver_name(cls) -> str:
        """
        The name of this driver.
        """
        return STR.shave

    @property
    def output(self) -> dict[str, Path]:
        """
        Returns a description of the file(s) created when this component runs.
        """
        return {"path": Path(self.config["config"]["output_grid_file"])}

    # Private helper methods

    @property
    def _input_config_path(self) -> Path:
        """
        Path to the input config file.
        """
        return self.rundir / "shave.cfg"

    @property
    def _runcmd(self):
        """
        The full command-line component invocation.
        """
        executable = self.config[STR.execution][STR.executable]
        return "%s < %s" % (executable, self._input_config_path.name)


set_driver_docstring(Shave)
