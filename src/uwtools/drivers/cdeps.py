"""
A driver for the CDEPS data models.
"""

from pathlib import Path

from iotaa import asset, task, tasks

from uwtools.api.template import _render
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
        Create data atmosphere configuration with all required content.
        """
        yield self._taskname("data atmosphere configuration")
        yield [
            self.atm_nml(),
            self.atm_stream(),
        ]

    @task
    def atm_nml(self):
        """
        Create data atmosphere Fortran namelist file (datm_in).
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
        Create data atmosphere stream config file (datm.streams).
        """
        fn = "datm.streams"
        yield self._taskname(f"stream file {fn}")
        path = self._rundir / fn
        yield asset(path, path.is_file)
        template_file = self._driver_config["atm_streams"]["template_file"]
        yield file(path=Path(template_file))
        self._model_stream_file("atm_streams", path, template_file)

    @tasks
    def ocn(self):
        """
        Create data ocean configuration with all required content.
        """
        yield self._taskname("data atmosphere configuration")
        yield [
            self.ocn_nml(),
            self.ocn_stream(),
        ]

    @task
    def ocn_nml(self):
        """
        Create data ocean Fortran namelist file (docn_in).
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
        Create data ocean stream config file (docn.streams).
        """
        fn = "docn.streams"
        yield self._taskname(f"stream file {fn}")
        path = self._rundir / fn
        yield asset(path, path.is_file)
        template_file = self._driver_config["ocn_streams"]["template_file"]
        yield file(path=Path(template_file))
        self._model_stream_file("ocn_streams", path, template_file)

    @tasks
    def provisioned_rundir(self):
        """
        Run directory provisioned with all required content.
        """
        yield self._taskname("provisioned run directory")
        yield [
            self.atm(),
            self.ocn(),
        ]

    # Private helper methods

    @property
    def _driver_name(self) -> str:
        """
        Returns the name of this driver.
        """
        return STR.cdeps

    def _model_namelist_file(self, group: str, path: Path) -> None:
        """
        Create an atmosphere or ocean namelist file.

        :param group: "atm_in" or "ocn_in".
        :param path: Path to write namelist to.
        """
        self._create_user_updated_config(
            config_class=NMLConfig, config_values=self._driver_config[group], path=path
        )

    def _model_stream_file(self, group: str, path: Path, template_file: str) -> None:
        """
        Create at atmosphere of ocean stream file, based on a template.

        :param group: "atm_in" or "ocn_in".
        :param path: Path to write namelist to.
        :param template_file: Path to the template file to render.
        """
        _render(
            input_file=Path(template_file),
            output_file=path,
            values_src=self._driver_config[group],
        )
