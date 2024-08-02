"""
A driver for the jedi component.
"""

import logging
from pathlib import Path

from iotaa import asset, refs, run, task, tasks

from uwtools.drivers.jedi_base import JEDIBase
from uwtools.drivers.support import set_driver_docstring
from uwtools.strings import STR
from uwtools.utils.tasks import file


class JEDI(JEDIBase):
    """
    A driver for the JEDI component.
    """

    # Workflow tasks

    @tasks
    def provisioned_rundir(self):
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
    def validate_only(self):
        """
        Validate JEDI config YAML.
        """
        taskname = self._taskname("validate_only")
        yield taskname
        a = asset(None, lambda: False)
        yield a
        executable = file(Path(self._driver_config[STR.execution][STR.executable]))
        config = self.configuration_file()
        yield [executable, config]
        cmd = "time %s --validate-only %s 2>&1" % (refs(executable), refs(config))
        if envcmds := self._driver_config[STR.execution].get(STR.envcmds):
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
        execution = self._driver_config[STR.execution]
        jedi_config = self._rundir / self._config_fn
        mpiargs = execution.get(STR.mpiargs, [])
        components = [
            execution.get(STR.mpicmd),  # MPI run program
            *[str(x) for x in mpiargs],  # MPI arguments
            execution[STR.executable],  # component executable name
            str(jedi_config),  # JEDI config file
        ]
        return " ".join(filter(None, components))


set_driver_docstring(JEDI)
