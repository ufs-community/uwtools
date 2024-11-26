"""
A driver for chgres_cube.
"""

from pathlib import Path

from iotaa import asset, task, tasks

from uwtools.config.formats.nml import NMLConfig
from uwtools.drivers.driver import DriverCycleLeadtimeBased
from uwtools.drivers.support import set_driver_docstring
from uwtools.strings import STR
from uwtools.utils.tasks import file


class ChgresCube(DriverCycleLeadtimeBased):
    """
    A driver for chgres_cube.
    """

    # Workflow tasks

    @task
    def namelist_file(self):
        """
        The namelist file.
        """
        fn = "fort.41"
        yield self.taskname(f"namelist file {fn}")
        path = self.rundir / fn
        yield asset(path, path.is_file)
        input_files = []
        namelist = self.config[STR.namelist]
        if base_file := namelist.get(STR.basefile):
            pathstr = ".".join([STR.namelist, STR.basefile])
            input_files.append((base_file, pathstr))
        if update_values := namelist.get(STR.updatevalues):
            config_files = update_values["config"]
            for k in ["mosaic_file_target_grid", "varmap_file", "vcoord_file_target_grid"]:
                pathstr = ".".join(["config", k])
                input_files.append((config_files[k], k))
            for k in [
                "atm_core_files_input_grid",
                "atm_files_input_grid",
                "atm_tracer_files_input_grid",
                "grib2_file_input_grid",
                "nst_files_input_grid",
                "sfc_files_input_grid",
            ]:
                if k in config_files:
                    grid_path = Path(config_files["data_dir_input_grid"])
                    v = config_files[k]
                    pathstr = ".".join(["config", k])
                    if isinstance(v, str):
                        input_files.append((grid_path / v, pathstr))
                    else:
                        input_files.extend([(grid_path / f, pathstr) for f in v])
            for k in [
                "orog_files_input_grid",
                "orog_files_target_grid",
            ]:
                if k in config_files:
                    grid_path = Path(config_files[k.replace("files", "dir")])
                    v = config_files[k]
                    pathstr = ".".join(["config", k])
                    if isinstance(v, str):
                        input_files.append((grid_path / v, pathstr))
                    else:
                        input_files.extend([(grid_path / f, pathstr) for f in v])
        yield [file(Path(input_file), pathstr) for input_file, pathstr in input_files]
        self._create_user_updated_config(
            config_class=NMLConfig,
            config_values=namelist,
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
            self.namelist_file(),
            self.runscript(),
        ]

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
            "KMP_AFFINITY": "scatter",
            "OMP_NUM_THREADS": self.config.get(STR.execution, {}).get(STR.threads, 1),
            "OMP_STACKSIZE": "1024m",
        }
        self._write_runscript(path=path, envvars=envvars)

    # Public helper methods

    @classmethod
    def driver_name(cls) -> str:
        """
        The name of this driver.
        """
        return STR.chgrescube


set_driver_docstring(ChgresCube)
