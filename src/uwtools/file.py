"""
File handling.
"""

import datetime as dt
from functools import cached_property
from pathlib import Path
from typing import Optional, Union

from iotaa import dryrun, tasks

from uwtools.config.formats.yaml import YAMLConfig
from uwtools.config.validator import validate_internal
from uwtools.exceptions import UWConfigError
from uwtools.logging import log
from uwtools.utils.api import str2path
from uwtools.utils.tasks import filecopy, symlink


class Stager:
    """
    The base class for staging files.
    """

    def __init__(
        self,
        config: Optional[Union[dict, Path]] = None,
        target_dir: Optional[Union[str, Path]] = None,
        cycle: Optional[dt.datetime] = None,
        leadtime: Optional[dt.timedelta] = None,
        keys: Optional[list[str]] = None,
        dry_run: bool = False,
    ) -> None:
        """
        Handle files.

        :param config: YAML-file path, or dict (read stdin if missing or None).
        :param target_dir: Path to target directory.
        :param cycle: A datetime object to make available for use in the config.
        :param leadtime: A timedelta object to make available for use in the config.
        :param keys: YAML keys leading to file dst/src block.
        :param dry_run: Do not copy files.
        :raises: UWConfigError if config fails validation.
        """
        dryrun(enable=dry_run)
        self._target_dir = str2path(target_dir)
        self._config = YAMLConfig(config=config)
        self._keys = keys or []
        self._config.dereference(
            context={
                **({"cycle": cycle} if cycle else {}),
                **({"leadtime": leadtime} if leadtime else {}),
                **self._config.data,
            }
        )
        self._validate()

    def _check_dst_paths(self, cfg: dict[str, str]) -> None:
        """
        Check that all destination paths are absolute if no target directory is specified.

        :parm cfg: The dst/linkname -> src/target map.
        :raises: UWConfigError if no target directory is specified and a relative path is.
        """
        if not self._target_dir:
            errmsg = "Relative path '%s' requires the target directory to be specified"
            for dst in cfg.keys():
                if not Path(dst).is_absolute():
                    raise UWConfigError(errmsg % dst)

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
                raise UWConfigError("Failed following YAML key(s): %s" % " -> ".join(nav))
            log.debug("Following config key '%s'", key)
            cfg = cfg[key]
        if not isinstance(cfg, dict):
            raise UWConfigError("No file map found at key path: %s" % " -> ".join(self._keys))
        self._check_dst_paths(cfg)
        return cfg

    def _validate(self) -> bool:
        """
        Validate config against its schema.

        :return: True if config passes validation.
        :raises: UWConfigError if config fails validation.
        """
        validate_internal(schema_name="files-to-stage", config=self._file_map)
        return True


class Copier(Stager):
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
        yield [filecopy(src=Path(v), dst=dst(k)) for k, v in self._file_map.items()]


class Linker(Stager):
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
        yield [symlink(target=Path(v), linkname=linkname(k)) for k, v in self._file_map.items()]
