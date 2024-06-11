"""
A driver for the FV3 model.
"""

from datetime import datetime
from pathlib import Path
from shutil import copy
from typing import List, Optional

from iotaa import asset, task, tasks

from uwtools.config.formats.nml import NMLConfig
from uwtools.config.formats.yaml import YAMLConfig
from uwtools.drivers.driver import Driver
from uwtools.logging import log
from uwtools.strings import STR
from uwtools.utils.tasks import file, filecopy, symlink


class FV3(Driver):
    """
    A driver for the FV3 model.
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

    @tasks
    def boundary_files(self):
        """
        Lateral boundary-condition files.
        """
        yield self._taskname("lateral boundary-condition files")
        lbcs = self._driver_config["lateral_boundary_conditions"]
        offset = abs(lbcs["offset"])
        endhour = self._driver_config["length"] + offset + 1
        interval = lbcs["interval_hours"]
        symlinks = {}
        for n in [7] if self._driver_config["domain"] == "global" else range(1, 7):
            for boundary_hour in range(offset, endhour, interval):
                target = Path(lbcs["path"].format(tile=n, forecast_hour=boundary_hour))
                linkname = (
                    self._rundir / "INPUT" / f"gfs_bndy.tile{n}.{(boundary_hour - offset):03d}.nc"
                )
                symlinks[target] = linkname
        yield [symlink(target=t, linkname=l) for t, l in symlinks.items()]

    @task
    def diag_table(self):
        """
        The diag_table file.
        """
        fn = "diag_table"
        yield self._taskname(fn)
        path = self._rundir / fn
        yield asset(path, path.is_file)
        yield None
        if src := self._driver_config.get(fn):
            path.parent.mkdir(parents=True, exist_ok=True)
            copy(src=src, dst=path)
        else:
            log.warning("No '%s' defined in config", fn)

    @task
    def field_table(self):
        """
        The field_table file.
        """
        fn = "field_table"
        yield self._taskname(fn)
        path = self._rundir / fn
        yield asset(path, path.is_file)
        yield filecopy(src=self._driver_config["field_table"]["base_file"], dst=path)

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
    def model_configure(self):
        """
        The model_configure file.
        """
        fn = "model_configure"
        yield self._taskname(fn)
        path = self._rundir / fn
        yield asset(path, path.is_file)
        base_file = self._driver_config["model_configure"].get("base_file")
        yield file(Path(base_file)) if base_file else None
        self._create_user_updated_config(
            config_class=YAMLConfig,
            config_values=self._driver_config["model_configure"],
            path=path,
        )

    @task
    def namelist_file(self):
        """
        The namelist file.
        """
        fn = "input.nml"
        yield self._taskname(fn)
        path = self._rundir / fn
        yield asset(path, path.is_file)
        base_file = self._driver_config["namelist"].get("base_file")
        yield file(Path(base_file)) if base_file else None
        self._create_user_updated_config(
            config_class=NMLConfig,
            config_values=self._driver_config["namelist"],
            path=path,
            schema=self._namelist_schema(),
        )

    @tasks
    def provisioned_run_directory(self):
        """
        Run directory provisioned with all required content.
        """
        yield self._taskname("provisioned run directory")
        required = [
            self.diag_table(),
            self.field_table(),
            self.files_copied(),
            self.files_linked(),
            self.model_configure(),
            self.namelist_file(),
            self.restart_directory(),
            self.runscript(),
        ]
        if self._driver_config["domain"] == "regional":
            required.append(self.boundary_files())
        yield required

    @task
    def restart_directory(self):
        """
        The RESTART directory.
        """
        yield self._taskname("RESTART directory")
        path = self._rundir / "RESTART"
        yield asset(path, path.is_dir)
        yield None
        path.mkdir(parents=True)

    @task
    def runscript(self):
        """
        The runscript.
        """
        path = self._runscript_path
        yield self._taskname(path.name)
        yield asset(path, path.is_file)
        yield None
        envvars = {
            "ESMF_RUNTIME_COMPLIANCECHECK": "OFF:depth=4",
            "KMP_AFFINITY": "scatter",
            "MPI_TYPE_DEPTH": 20,
            "OMP_NUM_THREADS": self._driver_config.get("execution", {}).get("threads", 1),
            "OMP_STACKSIZE": "512m",
        }
        self._write_runscript(path=path, envvars=envvars)

    # Private helper methods

    @property
    def _driver_name(self) -> str:
        """
        Returns the name of this driver.
        """
        return STR.fv3

    def _taskname(self, suffix: str) -> str:
        """
        Returns a common tag for graph-task log messages.

        :param suffix: Log-string suffix.
        """
        return self._taskname_with_cycle(self._cycle, suffix)
