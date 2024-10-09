"""
A driver for chgres_cube.
"""

from pathlib import Path

from iotaa import asset, task, tasks

from uwtools.config.formats.nml import NMLConfig
from uwtools.drivers.driver import DriverCycleBased
from uwtools.drivers.support import set_driver_docstring
from uwtools.strings import STR
from uwtools.utils.tasks import file


class ChgresCube(DriverCycleBased):
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
            input_files.append(base_file)
        if update_values := namelist.get(STR.updatevalues):
            config_files = update_values["config"]
            file_keys = [
                "atm_files_input_grid",
                "grib2_file_input_grid",
                "mosaic_file_target_grid",
                "nst_files_input_grid",
                "sfc_files_input_grid",
                "orog_files_input_grid",
                "orog_files_target_grid",
            ]
            path_keys = [
                "atm_core_files_input_grid",
                "atm_tracer_files_input_grid",
                "varmap_file",
                "vcoord_file_target_grid",
            ]
            dir_keys = [
                "data_dir_input_grid",
                "data_dir_input_grid",
                "fix_dir_target_grid",
                "data_dir_input_grid",
                "data_dir_input_grid",
                "orog_dir_input_grid",
                "orog_dir_target_grid",
            ]
            for file_key, dir_key in zip(file_keys, dir_keys):
                if file_key and dir_key in config_files:
                    v = config_files[file_key]
                    if isinstance(v, str):
                        full_path = Path(config_files[dir_key]) / config_files[file_key]
                        input_files.append(full_path)
                    else:
                        input_files += v
            for k in path_keys:
                if k in config_files:
                    v = config_files[k]
                    if isinstance(v, str):
                        input_files.append(v)
                    else:
                        input_files += v
        yield [file(Path(input_file)) for input_file in input_files]
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
