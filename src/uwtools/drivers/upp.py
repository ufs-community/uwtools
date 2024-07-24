"""
A driver for UPP.
"""

from pathlib import Path

from iotaa import asset, task, tasks

from uwtools.config.formats.nml import NMLConfig
from uwtools.drivers.driver import DriverCycleLeadtimeBased
from uwtools.strings import STR
from uwtools.utils.tasks import file, filecopy, symlink


class UPP(DriverCycleLeadtimeBased):
    """
    A driver for UPP.
    """

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

    @task
    def namelist_file(self):
        """
        The namelist file.
        """
        path = self._namelist_path
        yield self._taskname(str(path))
        yield asset(path, path.is_file)
        base_file = self._driver_config["namelist"].get("base_file")
        yield file(Path(base_file)) if base_file else None
        path.parent.mkdir(parents=True, exist_ok=True)
        self._create_user_updated_config(
            config_class=NMLConfig,
            config_values=self._driver_config["namelist"],
            path=path,
            schema=self._namelist_schema(),
        )

    @tasks
    def provisioned_rundir(self):
        """
        Run directory provisioned with all required content.
        """
        yield self._taskname("provisioned run directory")
        yield [
            self.files_copied(),
            self.files_linked(),
            self.namelist_file(),
            self.runscript(),
        ]

    # Private helper methods

    @property
    def _driver_name(self) -> str:
        """
        Returns the name of this driver.
        """
        return STR.upp

    @property
    def _namelist_path(self) -> Path:
        """
        Path to the namelist file.
        """
        return self._rundir / "itag"

    @property
    def _runcmd(self) -> str:
        """
        Returns the full command-line component invocation.
        """
        execution = self._driver_config.get("execution", {})
        mpiargs = execution.get("mpiargs", [])
        components = [
            execution.get("mpicmd"),
            *[str(x) for x in mpiargs],
            "%s < %s" % (execution["executable"], self._namelist_path.name),
        ]
        return " ".join(filter(None, components))
