"""
A UPP common mixin class.
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, ClassVar

from iotaa import asset, task, tasks

from uwtools.config.formats.nml import NMLConfig
from uwtools.strings import STR
from uwtools.utils.tasks import file, filecopy, symlink

if TYPE_CHECKING:
    from uwtools.config.formats.base import Config
    from uwtools.config.support import YAMLKey


class UPPCommon:
    """
    A UPP common mixin class.
    """

    # Facts specific to the supported UPP version:

    GENPROCTYPE_IDX = 8
    NFIELDS = 16
    NPARAMS = 42

    # Workflow tasks:

    @tasks
    def control_file(self):
        """
        The GRIB control file.
        """
        yield self.taskname("GRIB control file")
        yield filecopy(
            src=Path(self.config["control_file"]), dst=self.rundir / "postxconfig-NT.txt"
        )

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
    def namelist_file(self):
        """
        The namelist file.
        """
        path = self.namelist_path
        yield self.taskname(str(path))
        yield asset(path, path.is_file)
        base_file = self.config[STR.namelist].get(STR.basefile)
        yield file(Path(base_file)) if base_file else None
        self._create_user_updated_config(
            config_class=NMLConfig,
            config_values=self.config[STR.namelist],
            path=path,
            schema=self.namelist_schema(),
        )

    # Helper methods:

    @property
    def namelist_path(self) -> Path:
        """
        The path to the namelist file.
        """
        return self.rundir / "itag"

    # Placeholders to be overridden by mixing-in classes:

    config: ClassVar = {}

    @staticmethod
    def _create_user_updated_config(
        config_class: type[Config], config_values: dict, path: Path, schema: dict | None = None
    ) -> None:
        pass

    def namelist_schema(
        self, _config_keys: list[YAMLKey] | None = None, _schema_keys: list[str] | None = None
    ) -> dict:
        return {}

    @property
    def rundir(self) -> Path:
        return Path("/dev/null")

    def taskname(self, _: str | None = None) -> str:
        return "NA"
