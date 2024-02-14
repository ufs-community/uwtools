# pylint: disable=duplicate-code
"""
A driver for sfc_climo_gen.
"""

# import os
# import stat
# from datetime import datetime
from pathlib import Path

# from shutil import copy
from typing import Any, Dict

# from iotaa import asset, dryrun, external, task, tasks
from iotaa import dryrun

# from uwtools.config.formats.fieldtable import FieldTableConfig
# from uwtools.config.formats.nml import NMLConfig
# from uwtools.config.formats.yaml import YAMLConfig
from uwtools.drivers.driver import Driver

# from uwtools.logging import log
from uwtools.utils.file import resource_pathobj

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

    def _validate(self) -> None:
        """
        Perform all necessary schema validation.
        """
        for schema_file in ("sfc_climo_gen.jsonschema", "platform.jsonschema"):
            self._validate_one(resource_pathobj(schema_file))
