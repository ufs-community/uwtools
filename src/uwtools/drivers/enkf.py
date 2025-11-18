"""
A driver for the EnKF component.
"""

from __future__ import annotations

from pathlib import Path

from iotaa import Asset, collection, task

from uwtools.api.config import get_yaml_config
from uwtools.config.formats.nml import NMLConfig
from uwtools.drivers.driver import DriverCycleBased
from uwtools.drivers.stager import FileStager
from uwtools.drivers.support import set_driver_docstring
from uwtools.fs import Linker
from uwtools.strings import STR
from uwtools.utils.tasks import file


class EnKF(DriverCycleBased, FileStager):
    """
    A driver for EnKF.
    """

    # Workflow tasks

    @collection
    def background_files(self):
        """
        The ensemble background files.
        """
        yield self.taskname("background files")
        member_files = self.config["background_files"]["files"]
        ensemble_size = self.config["background_files"]["ensemble_size"]
        file_sets = []
        for member in range(1, ensemble_size + 1):
            file_set = get_yaml_config(member_files)
            file_set.dereference(
                context={
                    "member": member,
                    "cycle": self.cycle,
                }
            )
            file_sets.append(file_set)
        yield [
            Linker(
                config=files.as_dict(),
                target_dir=self.rundir,
            ).go()
            for files in file_sets
        ]

    @task
    def namelist_file(self):
        """
        The namelist file.
        """
        path = self._input_config_path
        yield self.taskname(path.name)
        yield Asset(path, path.is_file)
        base_file = self.config[STR.namelist].get(STR.basefile)
        yield file(Path(base_file)) if base_file else None
        self.create_user_updated_config(
            config_class=NMLConfig,
            config_values=self.config[STR.namelist],
            path=path,
            schema=self.namelist_schema(),
        )

    @collection
    def provisioned_rundir(self):
        """
        Run directory provisioned with all required content.
        """
        yield self.taskname("provisioned run directory")
        task_list = [
            self.background_files(),
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
        yield Asset(path, path.is_file)
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
        return STR.enkf

    # Private helper methods

    @property
    def _input_config_path(self) -> Path:
        """
        Path to the input config file.
        """
        return self.rundir / "enkf.nml"

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


set_driver_docstring(EnKF)
