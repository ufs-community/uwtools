"""
A driver for the jedi component.
"""

import logging
from datetime import datetime
from pathlib import Path

from iotaa import asset, dryrun, run, task, tasks

from uwtools.config.formats.yaml import YAMLConfig
from uwtools.drivers.driver import Driver
from uwtools.strings import STR
from uwtools.utils.tasks import file, filecopy, symlink


class JEDI(Driver):
    """
    A driver for the JEDI component.
    """

    def __init__(self, config: Path, cycle: datetime, dry_run: bool = False, batch: bool = False):
        """
        The driver.

        :param config: Path to config file.
        :param cycle: The forecast cycle.
        :param dry_run: Run in dry-run mode?
        :param batch: Run component via the batch system?
        """
        super().__init__(config=config, dry_run=dry_run, batch=batch, cycle=cycle)
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
    def validate_only(self):
        """
        Validate config.
        """
        taskname = self._taskname("validate_only")
        yield taskname

        a = asset(None, lambda: False)
        yield a
        path = Path(self._driver_config["configuration_file"]["base_file"])
        executable = Path(self._driver_config["execution"]["executable"])
        yield [file(executable), file(path)]
        env = " && ".join(self._driver_config["execution"]["envcmds"])
        cmd = "{env} && time {x} --validate-only {p} 2>&1".format(env=env, x=executable, p=path)
        result = run(taskname, cmd) 
        breakpoint()
        if result.success:
            logging.info("%s: Config is valid", taskname)
            a.ready = lambda: True

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

    # Private helper methods

    @property
    def _driver_name(self) -> str:
        """
        Returns the name of this driver.
        """
        return STR.jedi

    def _taskname(self, suffix: str) -> str:
        """
        Returns a common tag for graph-task log messages.

        :param suffix: Log-string suffix.
        """
        return "%s %s %s" % (self._cycle.strftime("%Y%m%d %HZ"), self._driver_name, suffix)
