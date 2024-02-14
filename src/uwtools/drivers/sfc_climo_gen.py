# pylint: disable=duplicate-code
# PM TRY TO FIX THIS ^^^
"""
A driver for sfc_climo_gen.
"""

# import os
# import stat
# from datetime import datetime
from pathlib import Path

# from shutil import copy
from typing import Any, Dict

from iotaa import asset, dryrun, task

# from uwtools.config.formats.fieldtable import FieldTableConfig
from uwtools.config.formats.nml import NMLConfig

# from uwtools.config.formats.yaml import YAMLConfig
from uwtools.drivers.driver import Driver

# from uwtools.logging import log
from uwtools.utils.file import resource_pathobj
from uwtools.utils.tasks import file

# from uwtools.utils.processing import execute


class SfcClimoGen(Driver):
    """
    A driver for sfc_climo_gen.
    """

    def __init__(self, config_file: Path, dry_run: bool = False, batch: bool = False):
        """
        The sfc_climo_gen driver.

        :param config_file: Path to config file.
        :param dry_run: Run in dry-run mode?
        :param batch: Run component via the batch system?
        """
        super().__init__(config_file=config_file, dry_run=dry_run, batch=batch)
        if self._dry_run:
            dryrun()
        self._rundir = Path(self._driver_config["run_dir"])

    # Workflow tasks

    @task
    def namelist_file(self):
        """
        The sfc_climo_gen namelist file.
        """
        fn = "fort.41"
        yield self._taskname(f"namelist file {fn}")
        path = self._rundir / fn
        yield asset(path, path.is_file)
        yield [
            file(path=Path(val))
            for key, val in self._driver_config["namelist"]["update_values"]["config"].items()
            if key.startswith("input_")
        ]
        self._create_user_updated_config(
            config_class=NMLConfig,
            config_values=self._driver_config.get("namelist", {}),
            path=path,
        )

    # Private helper methods

    @property
    def _driver_config(self) -> Dict[str, Any]:
        """
        Returns the config block specific to this driver.
        """
        driver_config: Dict[str, Any] = self._config["sfc_climo_gen"]
        return driver_config

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
        return "sfc_climo_gen %s" % suffix

    def _validate(self) -> None:
        """
        Perform all necessary schema validation.
        """
        for schema_file in ("sfc_climo_gen.jsonschema", "platform.jsonschema"):
            self._validate_one(resource_pathobj(schema_file))
