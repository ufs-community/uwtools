"""
A driver for orog_gsl.
"""

from pathlib import Path
from typing import List, Optional

from iotaa import asset, task, tasks

from uwtools.drivers.driver import Driver
from uwtools.strings import STR
from uwtools.utils.tasks import symlink


class OrogGSL(Driver):
    """
    A driver for orog_gsl.
    """

    def __init__(
        self,
        config: Optional[Path] = None,
        dry_run: bool = False,
        batch: bool = False,
        key_path: Optional[List[str]] = None,
    ):
        """
        The driver.

        :param config: Path to config file (read stdin if missing or None).
        :param dry_run: Run in dry-run mode?
        :param batch: Run component via the batch system?
        :param key_path: Keys leading through the config to the driver's configuration block.
        """
        super().__init__(config=config, dry_run=dry_run, batch=batch, key_path=key_path)

    # Workflow tasks

    @task
    def input_grid_file(self):
        """
        The input grid file.
        """
        path = Path(self._driver_config["config"]["input_grid_file"])
        yield self._taskname("Input grid")
        yield asset(path, path.is_file)
        yield symlink(target=path, linkname=Path(self._driver_config["run_dir"]) / path.name)

    @tasks
    def provisioned_run_directory(self):
        """
        Run directory provisioned with all required content.
        """
        yield self._taskname("provisioned run directory")
        yield [
            self.input_grid_file(),
            self.runscript(),
            self.topo_data_2p5m(),
            self.topo_data_30s(),
        ]

    @task
    def runscript(self):
        """
        The runscript.
        """
        path = self._runscript_path
        yield self._taskname(path.name)
        yield asset(path, path.is_file)
        yield None
        self._write_runscript(path)

    @task
    def topo_data_2p5m(self):
        """
        Global topographic data on 2.5-minute lat-lon grid.
        """
        path = Path(self._driver_config["config"]["topo_data_2p5m"])
        yield self._taskname("Global 2.5m topo data")
        yield asset(path, path.is_file)
        yield symlink(target=path, linkname=Path(self._driver_config["run_dir"]) / path.name)

    @task
    def topo_data_30s(self):
        """
        Global topographic data on 30-second lat-lon grid.
        """
        path = Path(self._driver_config["config"]["topo_data_30s"])
        yield self._taskname("Global 30s topo data")
        yield asset(path, path.is_file)
        yield symlink(target=path, linkname=Path(self._driver_config["run_dir"]) / path.name)

    # Private helper methods

    @property
    def _driver_name(self) -> str:
        """
        Returns the name of this driver.
        """
        return STR.oroggsl

    @property
    def _runcmd(self):
        """
        Returns the full command-line component invocation.
        """
        inputs = "\n".join(self._driver_config["config"][k] for k in ("tile", "resolution", "halo"))
        executable = self._driver_config["execution"]["executable"]
        return f"echo '%s' | %s" % (inputs, executable)
