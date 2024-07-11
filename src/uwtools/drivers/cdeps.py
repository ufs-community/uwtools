"""
A driver for the CDEPS data models.
"""

from pathlib import Path

from iotaa import asset, task, tasks

from uwtools.api.template import render
from uwtools.config.formats.nml import NMLConfig
from uwtools.drivers.driver import AssetsCycleBased
from uwtools.strings import STR
from uwtools.utils.tasks import file


class CDEPS(AssetsCycleBased):
    """
    A driver for the CDEPS data models.
    """

    # Workflow tasks

    @tasks
    def atm(self):
        """
        It creates data atmosphere configuration with all required content.
        """
        yield self._taskname("data atmosphere configuration")
        yield [
            self.atm_nml(),
            self.atm_stream(),
        ]

    @task
    def atm_nml(self):
        """
        It creates data atmosphere Fortran namelist file (datm_in).
        """
        fn = "datm_in"
        yield self._taskname(f"namelist file {fn}")
        path = self._rundir / fn
        yield asset(path, path.is_file)
        yield None
        path.parent.mkdir(parents=True, exist_ok=True)
        self._model_namelist_file("atm_in", path)

    @task
    def atm_stream(self):
        """
        It creates data atmosphere stream config file (datm.streams).
        """
        fn = "datm.streams"
        yield self._taskname(f"namelist file {fn}")
        path = self._rundir / fn
        yield asset(path, path.is_file)
        temp_path = self._driver_config["atm_streams"]["base_file"]
        yield file(path=Path(temp_path))
        self._model_stream_file("atm_streams", path, temp_path)

    @tasks
    def ocn(self):
        """
        It creates data ocean configuration with all required content.
        """
        yield self._taskname("data atmosphere configuration")
        yield [
            self.ocn_nml(),
            self.ocn_stream(),
        ]

    @task
    def ocn_nml(self):
        """
        It creates data ocean Fortran namelist file (docn_in).
        """
        fn = "docn_in"
        yield self._taskname(f"namelist file {fn}")
        path = self._rundir / fn
        yield asset(path, path.is_file)
        yield None
        path.parent.mkdir(parents=True, exist_ok=True)
        self._model_namelist_file("ocn_in", path)

    @task
    def ocn_stream(self):
        """
        It creates data ocean stream config file (docn.streams).
        """
        fn = "docn.streams"
        yield self._taskname(f"namelist file {fn}")
        path = self._rundir / fn
        yield asset(path, path.is_file)
        temp_path = self._driver_config["ocn_streams"]["base_file"]
        yield file(path=Path(temp_path))
        self._model_stream_file("ocn_streams", path, temp_path)

    # Private helper methods

    @property
    def _driver_name(self) -> str:
        """
        Returns the name of this driver.
        """
        return STR.cdeps

    def _model_namelist_file(self, group: str, path: Path) -> None:
        self._create_user_updated_config(
            config_class=NMLConfig, config_values=self._driver_config[group], path=path
        )

    def _model_stream_file(self, group: str, path: Path, template: str) -> None:
        render(input_file=Path(template), output_file=path, values_src=self._driver_config[group])

    def _taskname(self, suffix: str) -> str:
        """
        Returns a common tag for graph-task log messages.

        :param suffix: Log-string suffix.
        """
        return "%s %s %s" % (self._cycle.strftime("%Y%m%d %HZ"), self._driver_name, suffix)
