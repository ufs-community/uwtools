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

    @task
    def go(self):
        yield "go"
        yield asset(None, lambda: True)
        yield None

    @task
    def yaml_file(self):
        """
        The yaml file.
        """
        pass
#        fn = "jedi.yaml"
#        yield self._taskname(f"yaml file {fn}")
#        path = self._rundir / fn
#        yield asset(path, path.is_file)
#        vals = self._driver_config["yaml"]["update_values"]["config"]
#        input_paths = [Path(v) for k, v in vals.items() if k.startswith("input_")]
#        input_paths += [Path(vals["mosaic_file_mdl"])]
#        input_paths += [Path(vals["orog_dir_mdl"]) / fn for fn in vals["orog_files_mdl"]]
#        yield [file(input_path) for input_path in input_paths]
#        self._create_user_updated_config(
#            config_class=NMLConfig,
#            config_values=self._driver_config.get("namelist", {}),
#            path=path,
#        )


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
        pass
#        return "%s %s %s" % (self._cycle.strftime("%Y%m%d %HZ"), self._driver_name, suffix)

