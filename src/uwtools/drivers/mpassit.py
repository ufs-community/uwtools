"""
A driver for the MPASSIT component.
"""

from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory

from iotaa import asset, task, tasks

from uwtools.api.config import get_nml_config
from uwtools.config.formats.nml import NMLConfig
from uwtools.drivers.driver import DriverCycleLeadtimeBased
from uwtools.strings import STR
from uwtools.utils.tasks import file, filecopy, symlink


class MPASSIT(DriverCycleLeadtimeBased):
    """
    A driver for MPASSIT.
    """

    # Workflow tasks

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
        yield file(Path(base_file)) if base_file else None
        self.create_user_updated_config(
            config_class=NMLConfig,
            config_values=self.config[STR.namelist],
            path=path,
            schema=self.namelist_schema(),
        )

    @tasks
    def provisioned_rundir(self):
        """
        Run directory provisioned with all required content.
        """
        yield self.taskname("provisioned run directory")
        yield [
            self.files_copied(),
            self.files_linked(),
            self.namelist_file(),
            self.runscript(),
        ]

    # Public helper methods

    @classmethod
    def driver_name(cls) -> str:
        """
        The name of this driver.
        """
        return STR.mpassit

    @property
    def output(self) -> dict[str, Path] | dict[str, list[Path]]:
        """
        Returns a description of the file(s) created when this component runs.
        """
        with TemporaryDirectory() as path:
            nml = Path(path, self._input_config_path.name)
            self.create_user_updated_config(
                config_class=NMLConfig,
                config_values=self.config[STR.namelist],
                path=nml,
                schema=self.namelist_schema(),
            )
            namelist = get_nml_config(nml)
        return {"path": self.rundir / namelist["config"]["output_file"]}

    # Private helper methods

    @property
    def _input_config_path(self) -> Path:
        """
        Path to the input config file.
        """
        return self.rundir / "mpassit.nml"

    @property
    def _runcmd(self) -> str:
        """
        The full command-line component invocation.
        """
        execution = self.config.get(STR.execution, {})
        mpiargs = execution.get(STR.mpiargs, [])
        components = [
            execution.get(STR.mpicmd),  # MPI run program
            *[str(x) for x in mpiargs],  # MPI arguments
            execution[STR.executable],  # component executable name
            self._input_config_path.name,  # namelist name
        ]
        return " ".join(filter(None, components))
