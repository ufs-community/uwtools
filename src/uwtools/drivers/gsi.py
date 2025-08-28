"""
A driver for the GSI component.
"""

from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory

from iotaa import asset, task, tasks

from uwtools.api.config import get_nml_config, get_yaml_config
from uwtools.config.formats.nml import NMLConfig
from uwtools.drivers.driver import DriverCycleBased
from uwtools.drivers.support import set_driver_docstring
from uwtools.strings import STR
from uwtools.utils.tasks import file, filecopy, symlink


class GSI(DriverCycleBased):
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

    @tasks
    def files_copied(self):
        """
        Files copied for run.
        """
        yield self.taskname("files copied")
        yield [
            filecopy(src=Path(src), dst=self.rundir / dst)
            for dst, src in self.config.get("files_to_copy", {}).items()
        ]

    @tasks
    def files_linked(self):
        """
        Files linked for run.
        """
        yield self.taskname("files linked")
        yield [
            symlink(target=Path(target), linkname=self.rundir / linkname)
            for linkname, target in self.config.get("files_to_link", {}).items()
        ]

    @task
    def namelist_file(self):
        """
        The namelist file.
        """
        path = self._input_config_path
        yield self.taskname(path.name)
        yield asset(path, path.is_file)
        base_file = self.config[STR.namelist].get(STR.basefile)
        # add a dependency on anything that might require a namelist change.
        # are there enough ensemble files? etc.
        yield file(Path(base_file)) if base_file else None
        self.create_user_updated_config(
            config_class=NMLConfig,
            config_values=self.config[STR.namelist],
            path=path,
            schema=self.namelist_schema(),
        )
        obs_input = Path(self.config["obs_input_file"]).read_text()
        with open(path, "a", 



        #TODO: tack on the stupid section

    @tasks
    def provisioned_rundir(self):
        """
        Run directory provisioned with all required content.
        """
        yield self.taskname("provisioned run directory")
        task_list = [
            self.coupler_res(),
            self.files_copied(),
            self.files_linked(),
            self.namelist_file(),
            self.runscript(),
        ]
        yield task_list


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
        return self.rundir / "gsiparm.nml"


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
