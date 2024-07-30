"""
A driver for sfc_climo_gen.
"""

from pathlib import Path

from iotaa import asset, task, tasks

from uwtools.config.formats.nml import NMLConfig
from uwtools.drivers.driver import DriverTimeInvariant
from uwtools.strings import STR
from uwtools.utils.tasks import file


class SfcClimoGen(DriverTimeInvariant):
    """
    A driver for sfc_climo_gen.
    """

    # Workflow tasks

    @task
    def namelist_file(self):
        """
        The namelist file.
        """
        fn = "fort.41"
        yield self._taskname(f"namelist file {fn}")
        path = self._rundir / fn
        yield asset(path, path.is_file)
        vals = self._driver_config[STR.namelist][STR.updatevalues]["config"]
        input_paths = [Path(v) for k, v in vals.items() if k.startswith("input_")]
        input_paths += [Path(vals["mosaic_file_mdl"])]
        input_paths += [Path(vals["orog_dir_mdl"]) / fn for fn in vals["orog_files_mdl"]]
        yield [file(input_path) for input_path in input_paths]
        self._create_user_updated_config(
            config_class=NMLConfig,
            config_values=self._driver_config[STR.namelist],
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
            self.namelist_file(),
            self.runscript(),
        ]

    # Private helper methods

    @property
    def _driver_name(self) -> str:
        """
        Returns the name of this driver.
        """
        return STR.sfcclimogen
