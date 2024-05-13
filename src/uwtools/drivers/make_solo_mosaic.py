"""
A driver for make_solo_mosaic.
"""

from pathlib import Path
from typing import Optional

from iotaa import asset, dryrun, task, tasks

from uwtools.drivers.driver import Driver
from uwtools.strings import STR


class MakeSoloMosaic(Driver):
    """
    A driver for make_solo_mosaic.
    """

    def __init__(self, config: Optional[Path] = None, dry_run: bool = False, batch: bool = False):
        """
        The driver.

        :param config: Path to config file (read stdin if missing or None).
        :param dry_run: Run in dry-run mode?
        :param batch: Run component via the batch system?
        """
        super().__init__(config=config, dry_run=dry_run, batch=batch)
        if self._dry_run:
            dryrun()

    # Workflow tasks

    @tasks
    def provisioned_run_directory(self):
        """
        Run directory provisioned with all required content.
        """
        yield self._taskname("provisioned run directory")
        yield self.runscript()

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
        return STR.makesolomosaic

    @property
    def _runcmd(self):
        """
        Returns the full command-line component invocation.
        """
        executable = self._driver_config["execution"]["executable"]
        flags = " ".join(f"--{k} {v}" for k, v in self._driver_config["config"].items())
        return f"{executable} {flags}"

    def _taskname(self, suffix: str) -> str:
        """
        Returns a common tag for graph-task log messages.

        :param suffix: Log-string suffix.
        """
        return "%s %s" % (self._driver_name, suffix)
