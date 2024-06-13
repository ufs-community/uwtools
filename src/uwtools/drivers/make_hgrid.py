"""
A driver for make_hgrid.
"""

from pathlib import Path
from typing import List, Optional

from iotaa import asset, task, tasks

from uwtools.drivers.driver import Driver
from uwtools.strings import STR


class MakeHgrid(Driver):
    """
    A driver for make_hgrid.
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
        self._write_runscript(path)

    # Private helper methods

    @property
    def _driver_name(self) -> str:
        """
        Returns the name of this driver.
        """
        return STR.makehgrid

    @property
    def _runcmd(self):
        """
        Returns the full command-line component invocation.
        """
        executable = self._driver_config["execution"]["executable"]
        config = self._driver_config["config"]
        flags = []
        for k, v in config.items():
            if isinstance(v, bool):
                flags.append("--%s" % k)
            elif isinstance(v, list):
                flags.append("--%s %s" % (k, ",".join(map(str, v))))
            else:
                flags.append("--%s %s" % (k, v))
        return f"{executable} " + " ".join(flags)
