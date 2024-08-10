"""
File and directory staging.
"""

import datetime as dt
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional, Union

from iotaa import dryrun, tasks

from uwtools.config.formats.yaml import YAMLConfig
from uwtools.config.validator import validate_internal
from uwtools.exceptions import UWConfigError
from uwtools.logging import log
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
        keys: Optional[list[str]] = None,
        dry_run: bool = False,
    ) -> None:
        """
        Stage files and directories.

        :param config: YAML-file path, or dict (read stdin if missing or None).
        :param target_dir: Path to target directory.
        :param cycle: A datetime object to make available for use in the config.
        :param leadtime: A timedelta object to make available for use in the config.
        :param keys: YAML keys leading to file dst/src block.
        :param dry_run: Do not copy files.
        :raises: UWConfigError if config fails validation.
        """
        dryrun(enable=dry_run)
        self._keys = keys or []
        self._target_dir = str2path(target_dir)
        yaml_config = YAMLConfig(config=str2path(config))
        yaml_config.dereference(
            context={
                **({"cycle": cycle} if cycle else {}),
                **({"leadtime": leadtime} if leadtime else {}),
                **yaml_config.data,
            }
        )
        self._config = yaml_config.data
        self._set_config_block()
        self._check_paths()
        self._validate()

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

    def _set_config_block(self) -> None:
        """
        Navigate keys to a config block.

        :raises: UWConfigError if no target directory is specified and a relative path is.
        """
        cfg = self._config
        nav = []
        for key in self._keys:
            nav.append(key)
            if key not in cfg:
                raise UWConfigError("Failed following YAML key(s): %s" % " -> ".join(nav))
            log.debug("Following config key '%s'", key)
            cfg = cfg[key]
        if not isinstance(cfg, dict):
            msg = "Expected block not found at key path: %s" % " -> ".join(self._keys)
            raise UWConfigError(msg)
        self._config = cfg

    @property
    @abstractmethod
    def _dst_paths(self) -> list[str]:
        """
        Returns the paths to files or directories to create.
        """

    @property
    @abstractmethod
    def _schema(self) -> str:
        """
        Returns the name of the schema to use for config validation.
        """

    def _validate(self) -> None:
        """
        Validate config against its schema.

        :raises: UWConfigError if config fails validation.
        """
        validate_internal(schema_name=self._schema, config=self._config)


class DirectoryStager(Stager):
    """
    Stage directories.
    """

    @tasks
    def go(self):
        """
        Create directories.
        """
        yield "Directories"
        yield [directory(path=Path(path)) for path in self._config[STR.mkdir]]

    @property
    def _dst_paths(self) -> list[str]:
        """
        Returns the paths to directories to create.
        """
        paths: list[str] = self._config[STR.mkdir]
        return paths

    @property
    def _schema(self) -> str:
        """
        Returns the name of the schema to use for config validation.
        """
        return "stage-dirs"


class FileStager(Stager):
    """
    Stage files.
    """

    @property
    def _dst_paths(self) -> list[str]:
        """
        Returns the paths to files to create.
        """
        return list(self._config.keys())

    @property
    def _schema(self) -> str:
        """
        Returns the name of the schema to use for config validation.
        """
        return "stage-files"


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
