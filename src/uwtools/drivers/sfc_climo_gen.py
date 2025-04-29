"""
A driver for sfc_climo_gen.
"""

import re
from pathlib import Path

from iotaa import asset, task, tasks

from uwtools.config.formats.nml import NMLConfig
from uwtools.drivers.driver import DriverTimeInvariant
from uwtools.drivers.support import set_driver_docstring
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
        yield self.taskname(f"namelist file {fn}")
        path = self.rundir / fn
        yield asset(path, path.is_file)
        vals = self.config[STR.namelist][STR.updatevalues]["config"]
        input_paths = [Path(v) for k, v in vals.items() if k.startswith("input_")]
        input_paths += [Path(vals["mosaic_file_mdl"])]
        input_paths += [Path(vals["orog_dir_mdl"], fn) for fn in vals["orog_files_mdl"]]
        yield [file(input_path) for input_path in input_paths]
        self._create_user_updated_config(
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
            self.namelist_file(),
            self.runscript(),
        ]

    @property
    def output(self) -> dict[str, Path]:
        """
        Returns a description of the file(s) created when this component runs.
        """
        cfg = self.config["namelist"]["update_values"]["config"]
        n = cfg["halo"]
        keys = [m[1] for key in cfg if (m := re.match(r"^input_(.*)_file$", key))]
        return {key: self.rundir / f"{key}.tile7.halo{n}.nc" for key in keys}

    # Public helper methods

    @classmethod
    def driver_name(cls) -> str:
        """
        The name of this driver.
        """
        return STR.sfcclimogen


set_driver_docstring(SfcClimoGen)
