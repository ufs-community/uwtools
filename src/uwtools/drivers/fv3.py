"""
A driver for the FV3 model.
"""

from pathlib import Path

from iotaa import Asset, collection, task

from uwtools.api.template import render
from uwtools.config.formats.nml import NMLConfig
from uwtools.config.formats.yaml import YAMLConfig
from uwtools.drivers.driver import DriverCycleBased
from uwtools.drivers.stager import FileStager
from uwtools.drivers.support import set_driver_docstring
from uwtools.strings import STR
from uwtools.utils.tasks import file, filecopy, symlink


class FV3(DriverCycleBased, FileStager):
    """
    A driver for the FV3 model.
    """

    # Workflow tasks

    @collection
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
        for n in [7] if self.config["domain"] == "regional" else range(1, 7):
            for boundary_hour in range(offset, endhour, interval):
                target = Path(lbcs["path"].format(tile=n, forecast_hour=boundary_hour))
                linkname = (
                    self.rundir / "INPUT" / f"gfs_bndy.tile{n}.{(boundary_hour - offset):03d}.nc"
                )
                symlinks[target] = linkname
        yield [symlink(target=tgt, linkname=lnk) for tgt, lnk in symlinks.items()]

    @task
    def diag_table(self):
        """
        The diag_table file.
        """
        fn = "diag_table"
        yield self.taskname(fn)
        path = self.rundir / fn
        yield Asset(path, path.is_file)
        template_file = Path(self.config[fn]["template_file"])
        yield file(template_file)
        render(
            input_file=template_file,
            output_file=path,
            overrides={
                **self.config[fn].get("template_values", {}),
                "cycle": self.cycle,
            },
        )

    @task
    def field_table(self):
        """
        The field_table file.
        """
        fn = "field_table"
        yield self.taskname(fn)
        path = self.rundir / fn
        yield Asset(path, path.is_file)
        yield filecopy(src=Path(self.config["field_table"][STR.basefile]), dst=path)

    @task
    def model_configure(self):
        """
        The model_configure file.
        """
        fn = "model_configure"
        yield self.taskname(fn)
        path = self.rundir / fn
        yield Asset(path, path.is_file)
        base_file = self.config["model_configure"].get(STR.basefile)
        yield file(Path(base_file)) if base_file else None
        self.create_user_updated_config(
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
        required = [
            self.diag_table(),
            self.field_table(),
            self.files_copied(),
            self.files_hardlinked(),
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
        yield Asset(path, path.is_dir)
        yield None
        path.mkdir(parents=True)

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
            "ESMF_RUNTIME_COMPLIANCECHECK": "OFF:depth=4",
            "KMP_AFFINITY": "scatter",
            "MPI_TYPE_DEPTH": 20,
            "OMP_NUM_THREADS": self.config.get(STR.execution, {}).get(STR.threads, 1),
            "OMP_STACKSIZE": "512m",
        }
        self._write_runscript(path=path, envvars=envvars)

    # Public helper methods

    @classmethod
    def driver_name(cls) -> str:
        """
        The name of this driver.
        """
        return STR.fv3


set_driver_docstring(FV3)
