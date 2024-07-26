"""
API access to ``uwtools`` file-management tools.
"""

import datetime as dt
from pathlib import Path
from typing import Optional, Union

from iotaa import Asset

from uwtools.file import FileCopier, FileLinker
from uwtools.utils.api import ensure_data_source as _ensure_data_source
from uwtools.utils.api import str2path as _str2path


def copy(
    config: Optional[Union[Path, dict, str]] = None,
    target_dir: Optional[Union[Path, str]] = None,
    cycle: Optional[dt.datetime] = None,
    leadtime: Optional[dt.timedelta] = None,
    keys: Optional[list[str]] = None,
    dry_run: bool = False,
    stdin_ok: bool = False,
) -> bool:
    """
    Copy files.

    :param config: YAML-file path, or ``dict`` (read ``stdin`` if missing or ``None``).
    :param target_dir: Path to target directory.
    :param cycle: A datetime object to make available for use in the config.
    :param leadtime: A timedelta object to make available for use in the config.
    :param keys: YAML keys leading to file dst/src block.
    :param dry_run: Do not copy files.
    :param stdin_ok: OK to read from ``stdin``?
    :return: ``True`` if all copies were created.
    """
    copier = FileCopier(
        target_dir=Path(target_dir) if target_dir else None,
        config=_ensure_data_source(_str2path(config), stdin_ok),
        cycle=cycle,
        leadtime=leadtime,
        keys=keys,
        dry_run=dry_run,
    )
    assets: list[Asset] = copier.go()  # type: ignore
    return all(asset.ready() for asset in assets)


def link(
    config: Optional[Union[Path, dict, str]] = None,
    target_dir: Optional[Union[Path, str]] = None,
    cycle: Optional[dt.datetime] = None,
    leadtime: Optional[dt.timedelta] = None,
    keys: Optional[list[str]] = None,
    dry_run: bool = False,
    stdin_ok: bool = False,
) -> bool:
    """
    Link files.

    :param config: YAML-file path, or ``dict`` (read ``stdin`` if missing or ``None``).
    :param target_dir: Path to target directory.
    :param cycle: A datetime object to make available for use in the config.
    :param leadtime: A timedelta object to make available for use in the config.
    :param keys: YAML keys leading to file dst/src block.
    :param dry_run: Do not link files.
    :param stdin_ok: OK to read from ``stdin``?
    :return: ``True`` if all links were created.
    """
    linker = FileLinker(
        target_dir=Path(target_dir) if target_dir else None,
        config=_ensure_data_source(_str2path(config), stdin_ok),
        cycle=cycle,
        leadtime=leadtime,
        keys=keys,
        dry_run=dry_run,
    )
    assets: list[Asset] = linker.go()  # type: ignore
    return all(asset.ready() for asset in assets)


__all__ = ["FileCopier", "FileLinker", "copy", "link"]
