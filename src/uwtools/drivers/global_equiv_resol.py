"""
A driver for the global_equiv_resol component.
"""

from pathlib import Path
from typing import List, Optional

from iotaa import asset, external, task, tasks

from uwtools.drivers.driver import Driver
from uwtools.strings import STR


class GlobalEquivResol(Driver):
    """
    A driver for global_equiv_resol.
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

    @external
    def input_file(self):
        """
        Ensure the specified input grid file exists.
        """
        path = Path(self._driver_config["input_grid_file"])
        yield self._taskname(path.name)
        yield asset(path, path.is_file)

    @tasks
    def provisioned_run_directory(self):
        """
        Run directory provisioned with all required content.
        """
        yield self._taskname("provisioned run directory")
        yield [
            self.input_file(),
            self.runscript(),
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
        self._write_runscript(path=path, envvars={})

    # Private helper methods

    @property
    def _driver_name(self) -> str:
        """
        Returns the name of this driver.
        """
        return STR.globalequivresol

    @property
    def _runcmd(self):
        """
        Returns the full command-line component invocation.
        """
        executable = self._driver_config["execution"]["executable"]
        input_file_path = self._driver_config["input_grid_file"]
        return f"{executable} {input_file_path}"
