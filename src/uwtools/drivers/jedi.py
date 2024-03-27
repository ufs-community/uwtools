"""
A driver for the jedi component.
"""

import os
import stat
from datetime import datetime
from pathlib import Path
from typing import Any, Dict

from iotaa import asset, dryrun, task, tasks

from uwtools.config.formats.yaml import YAMLConfig
from uwtools.drivers.driver import Driver
from uwtools.strings import STR
from uwtools.utils.tasks import file


class Jedi(Driver):
    """
    A driver for the jedi component.
    """

    def __init__(
        self, config_file: Path, cycle: datetime, dry_run: bool = False, batch: bool = False
    ):
        """
        The driver.

        :param config_file: Path to config file.
        :param cycle: The forecast cycle.
        :param dry_run: Run in dry-run mode?
        :param batch: Run component via the batch system?
        """

        super().__init__(config_file=config_file, dry_run=dry_run, batch=batch)
        self._config.dereference(context={"cycle": cycle})
        if self._dry_run:
            dryrun()
        self._cycle = cycle

    # Workflow tasks


    @tasks
    def files_copied(self):
        """
        Files copied for run.
        """
        yield self._taskname("files copied")
        yield [
            filecopy(src=Path(src), dst=self._rundir / dst)
            for dst, src in self._driver_config.get("files_to_copy", {}).items()
        ]

    @tasks
    def files_linked(self):
        """
        Files linked for run.
        """
        yield self._taskname("files linked")
        yield [
            symlink(target=Path(target), linkname=self._rundir / linkname)
            for linkname, target in self._driver_config.get("files_to_link", {}).items()
        ]

    @tasks
    def provisioned_run_directory(self):
        """
        Run directory provisioned with all required content.
        """
        yield self._taskname("provisioned run directory")
        yield [
            self.files_copied(),
            self.files_linked(),
            self.yaml_file(),
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

    @task
    def yaml_file(self):
        """
        The yaml file.
        """
        fn = "input.yaml"
        yield self._taskname(fn)
        path = self._rundir / fn
        yield asset(path, path.is_file)
        yield None
        self._create_user_updated_config(
            config_class=YAMLConfig,
            config_values=self._driver_config.get("yaml", {}),
            path=path,
        )

    @task
    def validate(self):
        """
        Validate the YAML.
        """
        pass


    # Private helper methods

    @property
    def _driver_name(self) -> str:
        """
        Returns the name of this driver.
        """
        return STR.jedi

    @property
    def _resources(self) -> Dict[str, Any]:
        """
        Returns configuration data for the runscript.
        """
        return {
            "account": self._config["platform"]["account"],
            "rundir": self._rundir,
            "scheduler": self._config["platform"]["scheduler"],
            **self._driver_config.get("execution", {}).get("batchargs", {}),
        }

    def _taskname(self, suffix: str) -> str:
        """
        Returns a common tag for graph-task log messages.

        :param suffix: Log-string suffix.
        """
        return "%s %s %s" % (self._cycle.strftime("%Y%m%d %HZ"), self._driver_name, suffix)
