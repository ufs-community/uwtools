"""
A driver for the FV3 model.
"""

from pathlib import Path
from shutil import copy

from iotaa import asset, task, tasks

from uwtools.config.formats.nml import NMLConfig
from uwtools.config.formats.yaml import YAMLConfig
from uwtools.drivers.driver import DriverCycleBased
from uwtools.drivers.support import set_driver_docstring
from uwtools.logging import log
from uwtools.strings import STR
from uwtools.utils.tasks import file, filecopy, symlink


class FV3(DriverCycleBased):
    """
    A driver for the FV3 model.
    """

    # Workflow tasks

    @tasks
    def boundary_files(self):
        """
        Lateral boundary-condition files.
        """
        yield self.taskname("lateral boundary-condition files")
        lbcs = self.config["lateral_boundary_conditions"]
        offset = abs(lbcs["offset"])
        endhour = self.config["length"] + offset + 1
        interval = lbcs["interval_hours"]
        symlinks = {}
        for n in [7] if self.config["domain"] == "global" else range(1, 7):
            for boundary_hour in range(offset, endhour, interval):
                target = Path(lbcs["path"].format(tile=n, forecast_hour=boundary_hour))
                linkname = (
                    self.rundir / "INPUT" / f"gfs_bndy.tile{n}.{(boundary_hour - offset):03d}.nc"
                )
                symlinks[target] = linkname
        yield [symlink(target=t, linkname=l) for t, l in symlinks.items()]

    @task
    def diag_table(self):
        """
        The diag_table file.
        """
        fn = "diag_table"
        yield self.taskname(fn)
        path = self.rundir / fn
        yield asset(path, path.is_file)
        yield None
        if src := self.config.get(fn):
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
        yield self.taskname(fn)
        path = self.rundir / fn
        yield asset(path, path.is_file)
        yield filecopy(src=Path(self.config["field_table"][STR.basefile]), dst=path)

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
    def model_configure(self):
        """
        The model_configure file.
        """
        fn = "model_configure"
        yield self.taskname(fn)
        path = self.rundir / fn
        yield asset(path, path.is_file)
        base_file = self.config["model_configure"].get(STR.basefile)
        yield file(Path(base_file)) if base_file else None
        self._create_user_updated_config(
            config_class=YAMLConfig,
            config_values=self.config["model_configure"],
            path=path,
        )

    @task
    def namelist_file(self):
        """
        The namelist file.
        """
        fn = "input.nml"
        yield self.taskname(fn)
        path = self.rundir / fn
        yield asset(path, path.is_file)
        base_file = self.config[STR.namelist].get(STR.basefile)
        yield file(Path(base_file)) if base_file else None
        self._create_user_updated_config(
            config_class=NMLConfig,
            config_values=self.config[STR.namelist],
            path=path,
            schema=self._namelist_schema(),
        )

    @tasks
    def provisioned_rundir(self):
        """
        Run directory provisioned with all required content.
        """
        yield self.taskname("provisioned run directory")
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
        if self.config["domain"] == "regional":
            required.append(self.boundary_files())
        yield required

    @task
    def restart_directory(self):
        """
        The RESTART directory.
        """
        yield self.taskname("RESTART directory")
        path = self.rundir / "RESTART"
        yield asset(path, path.is_dir)
        yield None
        path.mkdir(parents=True)

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
            "ESMF_RUNTIME_COMPLIANCECHECK": "OFF:depth=4",
            "KMP_AFFINITY": "scatter",
            "MPI_TYPE_DEPTH": 20,
            "OMP_NUM_THREADS": self.config.get(STR.execution, {}).get(STR.threads, 1),
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


set_driver_docstring(FV3)
