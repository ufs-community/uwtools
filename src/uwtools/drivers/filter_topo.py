"""
A driver for filter_topo.
"""

from pathlib import Path
from typing import List, Optional

from iotaa import asset, task, tasks

from uwtools.drivers.driver import Driver
from uwtools.strings import STR
from uwtools.utils.tasks import symlink


class FilterTopo(Driver):
    """
    A driver for filter_topo.
    """

    def __init__(
        self,
        config: Optional[Path] = None,
        dry_run: bool = False,
        batch: bool = False,
        key_path: Optional[List[str]] = None,
    ):
        """
        The driver.

        :param config: Path to config file (read stdin if missing or None).
        :param dry_run: Run in dry-run mode?
        :param batch: Run component via the batch system?
        :param key_path: Keys leading through the config to the driver's configuration block.
        """
        super().__init__(config=config, dry_run=dry_run, batch=batch, key_path=key_path)

    # Workflow tasks

    @task
    def input_grid_file(self):
        """
        The input grid file.
        """
        fn = "C%s_grid.tile%s.halo%s.nc" % tuple(
            self._driver_config["config"][k] for k in ["resolution", "tile", "halo"]
        )
        src = Path(self._driver_config["config"]["input_grid_file"])
        dst = Path(self._driver_config["run_dir"]) / fn
        yield self._taskname("Input grid")
        yield asset(dst, dst.is_file)
        yield symlink(target=src, linkname=dst)

    @task
    def mosaic_file(self):
        """
        The mosaic file from the make_solo_mosaic program.
        """
        raise NotImplemented()
        # fn = "geo_em.d01.lat-lon.2.5m.HGT_M.nc"
        # src = Path(self._driver_config["config"]["topo_data_2p5m"])
        # dst = Path(self._driver_config["run_dir"]) / fn
        # yield self._taskname("Input grid")
        # yield asset(dst, dst.is_file)
        # yield symlink(target=src, linkname=dst)

    @task
    def namelist_file(self):
        """
        The namelist file.
        """
        raise NotImplemented()
        # fn = "fort.41"
        # yield self._taskname(f"namelist file {fn}")
        # path = self._rundir / fn
        # yield asset(path, path.is_file)
        # vals = self._driver_config["namelist"]["update_values"]["config"]
        # input_paths = [Path(v) for k, v in vals.items() if k.startswith("input_")]
        # input_paths += [Path(vals["mosaic_file_mdl"])]
        # input_paths += [Path(vals["orog_dir_mdl"]) / fn for fn in vals["orog_files_mdl"]]
        # yield [file(input_path) for input_path in input_paths]
        # self._create_user_updated_config(
        #     config_class=NMLConfig,
        #     config_values=self._driver_config["namelist"],
        #     path=path,
        #     schema=self._namelist_schema(),
        # )

    @task
    def orog_file(self):
        """
        The orography file from the orog program.
        """
        raise NotImplemented()
        # fn = "HGT.Beljaars_filtered.lat-lon.30s_res.nc"
        # src = Path(self._driver_config["config"]["topo_data_30s"])
        # dst = Path(self._driver_config["run_dir"]) / fn
        # yield self._taskname("Input grid")
        # yield asset(dst, dst.is_file)
        # yield symlink(target=src, linkname=dst)

    @tasks
    def provisioned_run_directory(self):
        """
        Run directory provisioned with all required content.
        """
        yield self._taskname("provisioned run directory")
        yield [
            self.input_grid_file(),
            self.mosaic_file(),
            self.namelist_file(),
            self.orog_file(),
            self.runscript(),
        ]

    @task
    def runscript(self):
        """
        The runscript.
        """
        path = self._runscript_path
        yield self._taskname(path.name)
        yield asset(path, path.is_file)
        yield None
        self._write_runscript(path)

    # Private helper methods

    @property
    def _driver_name(self) -> str:
        """
        Returns the name of this driver.
        """
        return STR.filtertopo

    @property
    def _runcmd(self):
        """
        Returns the full command-line component invocation.
        """
        raise NotImplemented()
        # inputs = [str(self._driver_config["config"][k]) for k in ("tile", "resolution", "halo")]
        # executable = self._driver_config["execution"]["executable"]
        # return "echo '%s' | %s" % ("\n".join(inputs), executable)
