"""
A driver for orog_gsl.
"""

from pathlib import Path
from typing import Optional

from iotaa import asset, task, tasks

from uwtools.drivers.driver import Driver
from uwtools.strings import STR
from uwtools.utils.tasks import symlink


class OrogGSL(Driver):
    """
    A driver for orog_gsl.
    """

    def __init__(
        self,
        config: Optional[Path] = None,
        dry_run: bool = False,
        batch: bool = False,
        key_path: Optional[list[str]] = None,
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

    @tasks
    def provisioned_run_directory(self):
        """
        Run directory provisioned with all required content.
        """
        yield self._taskname("provisioned run directory")
        yield [
            self.input_grid_file(),
            self.runscript(),
            self.topo_data_2p5m(),
            self.topo_data_30s(),
        ]

    @task
    def topo_data_2p5m(self):
        """
        Global topographic data on 2.5-minute lat-lon grid.
        """
        fn = "geo_em.d01.lat-lon.2.5m.HGT_M.nc"
        src = Path(self._driver_config["config"]["topo_data_2p5m"])
        dst = Path(self._driver_config["run_dir"]) / fn
        yield self._taskname("Input grid")
        yield asset(dst, dst.is_file)
        yield symlink(target=src, linkname=dst)

    @task
    def topo_data_30s(self):
        """
        Global topographic data on 30-second lat-lon grid.
        """
        fn = "HGT.Beljaars_filtered.lat-lon.30s_res.nc"
        src = Path(self._driver_config["config"]["topo_data_30s"])
        dst = Path(self._driver_config["run_dir"]) / fn
        yield self._taskname("Input grid")
        yield asset(dst, dst.is_file)
        yield symlink(target=src, linkname=dst)

    # Private helper methods

    @property
    def _driver_name(self) -> str:
        """
        Returns the name of this driver.
        """
        return STR.oroggsl

    @property
    def _runcmd(self):
        """
        Returns the full command-line component invocation.
        """
        inputs = [str(self._driver_config["config"][k]) for k in ("tile", "resolution", "halo")]
        executable = self._driver_config["execution"]["executable"]
        return "echo '%s' | %s" % ("\n".join(inputs), executable)
