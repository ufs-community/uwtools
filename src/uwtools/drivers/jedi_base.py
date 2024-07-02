"""
A base class for jedi-based drivers.
"""

from abc import abstractmethod
from datetime import datetime
from pathlib import Path
from typing import Optional

from iotaa import asset, task, tasks

from uwtools.config.formats.yaml import YAMLConfig
from uwtools.drivers.driver import Driver
from uwtools.utils.tasks import file, filecopy, symlink


class JEDIBase(Driver):
    """
    A base class for the JEDI-like drivers.
    """

    def __init__(
        self,
        cycle: datetime,
        config: Optional[Path] = None,
        dry_run: bool = False,
        batch: bool = False,
        key_path: Optional[list[str]] = None,
    ):
        """
        The driver.

        :param cycle: The forecast cycle.
        :param config: Path to config file.
        :param dry_run: Run in dry-run mode?
        :param batch: Run component via the batch system?
        :param key_path: Keys leading through the config to the driver's configuration block.
        """
        super().__init__(
            config=config, dry_run=dry_run, batch=batch, cycle=cycle, key_path=key_path
        )

    # Workflow tasks

    @task
    def configuration_file(self):
        """
        The executable's YAML configuration file.
        """
        fn = self._config_fn
        yield self._taskname(fn)
        path = self._rundir / fn
        yield asset(path, path.is_file)
        base_file = self._driver_config["configuration_file"].get("base_file")
        yield file(Path(base_file)) if base_file else None
        self._create_user_updated_config(
            config_class=YAMLConfig,
            config_values=self._driver_config["configuration_file"],
            path=path,
        )

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
    @abstractmethod
    def provisioned_run_directory(self):
        """
        Run directory provisioned with all required content.
        """

    # Private helper methods

    @property
    @abstractmethod
    def _config_fn(self) -> str:
        """
        Returns the name of the config file used in execution.
        """

    def _taskname(self, suffix: str) -> str:
        """
        Returns a common tag for graph-task log messages.

        :param suffix: Log-string suffix.
        """
        return self._taskname_with_cycle(suffix)
