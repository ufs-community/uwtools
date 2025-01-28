"""
API access to ``uwtools`` file and directory management tools.
"""

import datetime as dt
from pathlib import Path
from typing import Optional, Union, cast

import iotaa

from uwtools.config.support import YAMLKey
from uwtools.fs import Copier, Linker, MakeDirs
from uwtools.utils.api import ensure_data_source as _ensure_data_source


def copy(
    config: Optional[Union[Path, dict, str]] = None,
    target_dir: Optional[Union[Path, str]] = None,
    cycle: Optional[dt.datetime] = None,
    leadtime: Optional[dt.timedelta] = None,
    key_path: Optional[list[YAMLKey]] = None,
    dry_run: bool = False,
    stdin_ok: bool = False,
) -> bool:
    """
    Copy files.

    :param config: YAML-file path, or ``dict`` (read ``stdin`` if missing or ``None``).
    :param target_dir: Path to target directory.
    :param cycle: A datetime object to make available for use in the config.
    :param leadtime: A timedelta object to make available for use in the config.
    :param key_path: Path of keys to config block to use.
    :param dry_run: Do not copy files.
    :param stdin_ok: OK to read from ``stdin``?
    :return: ``True`` if all copies were created.
    """
    stager = Copier(
        target_dir=Path(target_dir) if target_dir else None,
        config=_ensure_data_source(config, stdin_ok),
        cycle=cycle,
        leadtime=leadtime,
        key_path=key_path,
    )
    assets = cast(list, iotaa.assets(stager.go(dry_run=dry_run)))
    return all(asset.ready() for asset in assets)


def link(
    config: Optional[Union[Path, dict, str]] = None,
    target_dir: Optional[Union[Path, str]] = None,
    cycle: Optional[dt.datetime] = None,
    leadtime: Optional[dt.timedelta] = None,
    key_path: Optional[list[YAMLKey]] = None,
    dry_run: bool = False,
    stdin_ok: bool = False,
) -> bool:
    """
    Link files.

    :param config: YAML-file path, or ``dict`` (read ``stdin`` if missing or ``None``).
    :param target_dir: Path to target directory.
    :param cycle: A datetime object to make available for use in the config.
    :param leadtime: A timedelta object to make available for use in the config.
    :param key_path: Path of keys to config block to use.
    :param dry_run: Do not link files.
    :param stdin_ok: OK to read from ``stdin``?
    :return: ``True`` if all links were created.
    """
    stager = Linker(
        target_dir=Path(target_dir) if target_dir else None,
        config=_ensure_data_source(config, stdin_ok),
        cycle=cycle,
        leadtime=leadtime,
        key_path=key_path,
    )
    assets = cast(list, iotaa.assets(stager.go(dry_run=dry_run)))
    return all(asset.ready() for asset in assets)


def makedirs(
    config: Optional[Union[Path, dict, str]] = None,
    target_dir: Optional[Union[Path, str]] = None,
    cycle: Optional[dt.datetime] = None,
    leadtime: Optional[dt.timedelta] = None,
    key_path: Optional[list[YAMLKey]] = None,
    dry_run: bool = False,
    stdin_ok: bool = False,
) -> bool:
    """
    Make directories.

    :param config: YAML-file path, or ``dict`` (read ``stdin`` if missing or ``None``).
    :param target_dir: Path to target directory.
    :param cycle: A datetime object to make available for use in the config.
    :param leadtime: A timedelta object to make available for use in the config.
    :param key_path: Path of keys to config block to use.
    :param dry_run: Do not link files.
    :param stdin_ok: OK to read from ``stdin``?
    :return: ``True`` if all directories were made.
    """
    stager = MakeDirs(
        target_dir=Path(target_dir) if target_dir else None,
        config=_ensure_data_source(config, stdin_ok),
        cycle=cycle,
        leadtime=leadtime,
        key_path=key_path,
    )
    assets = cast(list, iotaa.assets(stager.go(dry_run=dry_run)))
    return all(asset.ready for asset in assets)


__all__ = ["Copier", "Linker", "MakeDirs", "copy", "link", "makedirs"]
