"""
A driver for the jedi component.
"""

import logging
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from iotaa import asset, refs, run, task, tasks

from uwtools.config.formats.yaml import YAMLConfig
from uwtools.drivers.driver import Driver
from uwtools.strings import STR
from uwtools.utils.tasks import file, filecopy, symlink


class JEDI(Driver):
    """
    A driver for the JEDI component.
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

        :param cycle: The forecast cycle.
        :param config: Path to config file.
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
    def configuration_file(self):
        """
        The JEDI YAML configuration file.
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
    def provisioned_run_directory(self):
        """
        Run directory provisioned with all required content.
        """
        yield self._taskname("provisioned run directory")
        yield [
            self.configuration_file(),
            self.files_copied(),
            self.files_linked(),
            self.runscript(),
            self.validate_only(),
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
        Validate JEDI config YAML.
        """
        taskname = self._taskname("validate_only")
        yield taskname
        a = asset(None, lambda: False)
        yield a
        executable = file(Path(self._driver_config["execution"]["executable"]))
        config = self.configuration_file()
        yield [executable, config]
        cmd = "time %s --validate-only %s 2>&1" % (refs(executable), refs(config))
        if envcmds := self._driver_config["execution"].get("envcmds"):
            cmd = " && ".join([*envcmds, cmd])
        result = run(taskname, cmd)
        if result.success:
            logging.info("%s: Config is valid", taskname)
            a.ready = lambda: True

    # Private helper methods

    @property
    def _config_fn(self) -> str:
        """
        Returns the name of the config file used in execution.
        """
        return "jedi.yaml"

    @property
    def _driver_name(self) -> str:
        """
        Returns the name of this driver.
        """
        return STR.jedi

    @property
    def _runcmd(self) -> str:
        """
        Returns the full command-line component invocation.
        """
        execution = self._driver_config.get("execution", {})
        jedi_config = self._rundir / self._config_fn
        mpiargs = execution.get("mpiargs", [])
        components = [
            execution.get("mpicmd"),  # MPI run program
            *[str(x) for x in mpiargs],  # MPI arguments
            execution["executable"],  # component executable name
            str(jedi_config),  # JEDI config file
        ]
        return " ".join(filter(None, components))

    def _taskname(self, suffix: str) -> str:
        """
        Returns a common tag for graph-task log messages.

        :param suffix: Log-string suffix.
        """
        return self._taskname_with_cycle(self._cycle, suffix)
