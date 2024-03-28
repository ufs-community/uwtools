"""
File handling.
"""

from functools import cached_property
from pathlib import Path
from typing import List, Optional, Union

from iotaa import tasks

from uwtools.config.formats.yaml import YAMLConfig
from uwtools.config.validator import validate_internal
from uwtools.exceptions import UWConfigError
from uwtools.logging import log
from uwtools.utils.tasks import filecopy, symlink


class FileStager:
    """
    The base class for staging files.
    """

    def __init__(
        self,
        target_dir: Path,
        config: Optional[Union[dict, Path]] = None,
        keys: Optional[List[str]] = None,
        dry_run: bool = False,
    ) -> None:
        """
        Handle files.

        :param target_dir: Path to target directory
        :param config: YAML-file path, or dict (read stdin if missing or None).
        :param keys: YAML keys leading to file dst/src block
        :param dry_run: Do not copy files
        :raises: UWConfigError if config fails validation.
        """
        self._target_dir = target_dir
        self._config = YAMLConfig(config=config)
        self._keys = keys or []
        self._dry_run = dry_run
        self._config.dereference()
        self._validate()

    @cached_property
    def _file_map(self) -> dict:
        """
        Navigate keys to file dst/src config block.

        :return: The dst/src file block from a potentially larger config.
        """
        cfg = self._config.data
        nav = []
        for key in self._keys:
            nav.append(key)
            if key not in cfg:
                raise UWConfigError("Config navigation %s failed" % " -> ".join(nav))
            log.debug("Following config key '%s'", key)
            cfg = cfg[key]
        return cfg

    def _validate(self) -> bool:
        """
        Validate config against its schema.

        :return: True if config passes validation.
        :raises: UWConfigError if config fails validation.
        """
        validate_internal(schema_name="files-to-stage", config=self._file_map)
        return True


class FileCopier(FileStager):
    """
    Stage files by copying.
    """

    @tasks
    def go(self):
        """
        Copy files.
        """
        yield "File copies"
        yield [filecopy(src=Path(v), dst=self._target_dir / k) for k, v in self._file_map.items()]


class FileLinker(FileStager):
    """
    Stage files by linking.
    """

    @tasks
    def go(self):
        """
        Link files.
        """
        yield "File links"
        yield [
            symlink(target=Path(v), linkname=self._target_dir / k)
            for k, v in self._file_map.items()
        ]
