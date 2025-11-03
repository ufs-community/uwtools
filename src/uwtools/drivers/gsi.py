"""
A driver for the GSI component.
"""

from __future__ import annotations

from pathlib import Path

from iotaa import asset, task, tasks

from uwtools.api.template import render
from uwtools.config.formats.nml import NMLConfig
from uwtools.drivers.driver import DriverCycleBased
from uwtools.drivers.stager import FileStager
from uwtools.drivers.support import set_driver_docstring
from uwtools.strings import STR
from uwtools.utils.tasks import file


class GSI(DriverCycleBased, FileStager):
    """
    A driver for GSI.
    """

    # Workflow tasks

    @task
    def coupler_res(self):
        """
        The coupler.res file.
        """
        fn = "coupler.res"
        yield self.taskname(fn)
        path = self.rundir / fn
        yield asset(path, path.is_file)
        template_file = Path(self.config[fn]["template_file"])
        yield file(template_file)
        render(
            input_file=template_file,
            output_file=path,
            overrides={
                **self.config[fn].get("template_values", {}),
            },
        )

    @task
    def namelist_file(self):
        """
        The namelist file.
        """
        path = self._input_config_path
        yield self.taskname(path.name)
        yield asset(path, path.is_file)
        base_file = self.config[STR.namelist].get(STR.basefile)
        yield file(Path(base_file)) if base_file else None
        self.create_user_updated_config(
            config_class=NMLConfig,
            config_values=self.config[STR.namelist],
            path=path,
            schema=self.namelist_schema(),
        )
        obs_input = Path(self.config["obs_input_file"]).read_text()
        with path.open(mode="a") as nml:
            nml.write(obs_input)

    @tasks
    def provisioned_rundir(self):
        """
        Run directory provisioned with all required content.
        """
        yield self.taskname("provisioned run directory")
        task_list = [
            self.coupler_res(),
            self.files_copied(),
            self.files_hardlinked(),
            self.files_linked(),
            self.namelist_file(),
            self.runscript(),
        ]
        yield task_list

    @task
    def runscript(self):
        """
        The runscript.
        """
        path = self._runscript_path
        yield self.taskname(path.name)
        yield asset(path, path.is_file)
        yield None
        envvars = {
            "OMP_NUM_THREADS": self.config.get(STR.execution, {}).get(STR.threads, 1),
            "OMP_STACKSIZE": self.config.get(STR.execution, {}).get(STR.stacksize, "1024M"),
        }
        self._write_runscript(path=path, envvars=envvars)

    # Public helper methods

    @classmethod
    def driver_name(cls) -> str:
        """
        The name of this driver.
        """
        return STR.gsi

    # Private helper methods

    @property
    def _input_config_path(self) -> Path:
        """
        Path to the input config file.
        """
        return self.rundir / "gsiparm.anl"

    @property
    def _runcmd(self) -> str:
        """
        The full command-line component invocation.
        """
        execution = self.config.get(STR.execution, {})
        mpiargs = execution.get(STR.mpiargs, [])
        components = [
            execution.get(STR.mpicmd),
            *[str(x) for x in mpiargs],
            "%s < %s" % (execution[STR.executable], self._input_config_path),
        ]
        return " ".join(filter(None, components))


set_driver_docstring(GSI)
