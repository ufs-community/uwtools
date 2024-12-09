"""
File and directory staging.
"""

import datetime as dt
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional, Union

from iotaa import dryrun, tasks

from uwtools.config.formats.yaml import YAMLConfig
from uwtools.config.tools import walk_key_path
from uwtools.config.validator import validate_internal
from uwtools.exceptions import UWConfigError
from uwtools.strings import STR
from uwtools.utils.api import str2path
from uwtools.utils.tasks import directory, filecopy, symlink


class Stager(ABC):
    """
    The base class for staging files and directories.
    """

    def __init__(
        self,
        config: Optional[Union[dict, str, Path]] = None,
        target_dir: Optional[Union[str, Path]] = None,
        cycle: Optional[dt.datetime] = None,
        leadtime: Optional[dt.timedelta] = None,
        key_path: Optional[list[Union[str, int]]] = None,
        dry_run: bool = False,
    ) -> None:
        """
        Stage files and directories.

        :param config: YAML-file path, or ``dict`` (read ``stdin`` if missing or ``None``).
        :param target_dir: Path to target directory.
        :param cycle: A ``datetime`` object to make available for use in the config.
        :param leadtime: A ``timedelta`` object to make available for use in the config.
        :param key_path: Path of keys to config block to use.
        :param dry_run: Do not copy files.
        :raises: ``UWConfigError`` if config fails validation.
        """
        dryrun(enable=dry_run)
        self._key_path = key_path or []
        self._target_dir = str2path(target_dir)
        yaml_config = YAMLConfig(config=str2path(config))
        yaml_config.dereference(
            context={
                **({"cycle": cycle} if cycle else {}),
                **({"leadtime": leadtime} if leadtime else {}),
                **yaml_config.data,
            }
        )
        self._config, _ = walk_key_path(yaml_config.data, self._key_path)
        self._validate()
        self._check_paths()

    def _check_paths(self) -> None:
        """
        Check that all paths are absolute if no target directory is specified.

        :parm paths: The paths to check.
        :raises: UWConfigError if no target directory is specified and a relative path is.
        """
        if not self._target_dir:
            errmsg = "Relative path '%s' requires the target directory to be specified"
            for dst in self._dst_paths:
                if not Path(dst).is_absolute():
                    raise UWConfigError(errmsg % dst)

    @property
    @abstractmethod
    def _dst_paths(self) -> list[str]:
        """
        The paths to files or directories to create.
        """

    @property
    @abstractmethod
    def _schema(self) -> str:
        """
        The name of the schema to use for config validation.
        """

    def _validate(self) -> None:
        """
        Validate config against its schema.

        :raises: UWConfigError if config fails validation.
        """
        validate_internal(schema_name=self._schema, desc="fs config", config=self._config)


class FileStager(Stager):
    """
    Stage files.
    """

    @property
    def _dst_paths(self) -> list[str]:
        """
        The paths to files to create.
        """
        return list(self._config.keys())

    @property
    def _schema(self) -> str:
        """
        The name of the schema to use for config validation.
        """
        return "files-to-stage"


class Copier(FileStager):
    """
    Stage files by copying.
    """

    @tasks
    def go(self):
        """
        Copy files.
        """
        dst = lambda k: Path(self._target_dir / k if self._target_dir else k)
        yield "File copies"
        yield [filecopy(src=Path(v), dst=dst(k)) for k, v in self._config.items()]


class Linker(FileStager):
    """
    Stage files by linking.
    """

    @tasks
    def go(self):
        """
        Link files.
        """
        linkname = lambda k: Path(self._target_dir / k if self._target_dir else k)
        yield "File links"
        yield [symlink(target=Path(v), linkname=linkname(k)) for k, v in self._config.items()]


class MakeDirs(Stager):
    """
    Make directories.
    """

    @tasks
    def go(self):
        """
        Make directories.
        """
        yield "Directories"
        yield [
            directory(path=Path(self._target_dir / p if self._target_dir else p))
            for p in self._config[STR.makedirs]
        ]

    @property
    def _dst_paths(self) -> list[str]:
        """
        The paths to directories to create.
        """
        paths: list[str] = self._config[STR.makedirs]
        return paths

    @property
    def _schema(self) -> str:
        """
        The name of the schema to use for config validation.
        """
        return "makedirs"
