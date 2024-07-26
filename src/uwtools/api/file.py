"""
API access to ``uwtools`` file-management tools.
"""

import datetime as dt
from pathlib import Path
from typing import Optional, Union

from uwtools.file import FileCopier as _FileCopier
from uwtools.file import FileLinker as _FileLinker
from uwtools.utils.api import ensure_data_source as _ensure_data_source
from uwtools.utils.api import str2path as _str2path


def copy(
    target_dir: Union[Path, str],
    config: Optional[Union[Path, dict, str]] = None,
    cycle: Optional[dt.datetime] = None,
    leadtime: Optional[dt.timedelta] = None,
    keys: Optional[list[str]] = None,
    dry_run: bool = False,
    stdin_ok: bool = False,
) -> bool:
    """
    Copy files.

    :param target_dir: Path to target directory.
    :param config: YAML-file path, or ``dict`` (read ``stdin`` if missing or ``None``).
    :param cycle: A datetime object to make available for use in the config.
    :param leadtime: A timedelta object to make available for use in the config.
    :param keys: YAML keys leading to file dst/src block.
    :param dry_run: Do not copy files.
    :param stdin_ok: OK to read from ``stdin``?
    :return: ``True`` if all files were copied.
    """
    _FileCopier(
        target_dir=Path(target_dir),
        config=_ensure_data_source(_str2path(config), stdin_ok),
        cycle=cycle,
        leadtime=leadtime,
        keys=keys,
        dry_run=dry_run,
    ).go()
    return True


def link(
    target_dir: Union[Path, str],
    config: Optional[Union[Path, dict, str]] = None,
    cycle: Optional[dt.datetime] = None,
    leadtime: Optional[dt.timedelta] = None,
    keys: Optional[list[str]] = None,
    dry_run: bool = False,
    stdin_ok: bool = False,
) -> bool:
    """
    Link files.

    :param target_dir: Path to target directory.
    :param config: YAML-file path, or ``dict`` (read ``stdin`` if missing or ``None``).
    :param cycle: A datetime object to make available for use in the config.
    :param leadtime: A timedelta object to make available for use in the config.
    :param keys: YAML keys leading to file dst/src block.
    :param dry_run: Do not link files.
    :param stdin_ok: OK to read from ``stdin``?
    :return: ``True`` if no exception is raised.
    """
    _FileLinker(
        target_dir=Path(target_dir),
        config=_ensure_data_source(_str2path(config), stdin_ok),
        cycle=cycle,
        leadtime=leadtime,
        keys=keys,
        dry_run=dry_run,
    ).go()
    return True
