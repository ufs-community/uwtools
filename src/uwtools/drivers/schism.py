"""
An assets driver for SCHISM.
"""

from datetime import datetime
from pathlib import Path
from typing import List, Optional

from iotaa import asset, task, tasks

from uwtools.api.template import render
from uwtools.drivers.driver import Assets
from uwtools.strings import STR
from uwtools.utils.tasks import file


class SCHISM(Assets):
    """
    An assets driver for SCHISM.
    """

    def __init__(
        self,
        cycle: datetime,
        config: Optional[Path] = None,
        dry_run: bool = False,
        batch: bool = False,
        key_path: Optional[List[str]] = None,
    ):
        """
        The driver.

        :param cycle: The cycle.
        :param config: Path to config file (read stdin if missing or None).
        :param dry_run: Run in dry-run mode?
        :param batch: Run component via the batch system?
        :param key_path: Keys leading through the config to the driver's configuration block.
        """
        super().__init__(
            config=config, dry_run=dry_run, batch=batch, cycle=cycle, key_path=key_path
        )
        self._cycle = cycle

    # Workflow tasks

    @task
    def namelist_file(self):
        """
        Render the namelist from the template file.
        """
        fn = "param.nml"
        yield self._taskname(fn)
        path = self._rundir / fn
        yield asset(path, path.is_file)
        template_file = Path(self._driver_config["namelist"]["template_file"])
        yield file(path=template_file)
        render(
            input_file=template_file,
            output_file=path,
            overrides=self._driver_config["namelist"]["template_values"],
        )

    @tasks
    def provisioned_run_directory(self):
        """
        Run directory provisioned with all required content.
        """
        yield self._taskname("provisioned run directory")
        yield self.namelist_file()

    # Private helper methods

    @property
    def _driver_name(self) -> str:
        """
        Returns the name of this driver.
        """
        return STR.schism
