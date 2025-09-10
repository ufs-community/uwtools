"""
API access to ``uwtools`` file and directory management tools.
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, cast

from uwtools.fs import Copier, Linker, MakeDirs
from uwtools.strings import STR
from uwtools.utils.api import ensure_data_source as _ensure_data_source

if TYPE_CHECKING:
    import datetime as dt

    from uwtools.config.support import YAMLKey


def copy(
    config: Path | dict | str | None = None,
    target_dir: Path | str | None = None,
    cycle: dt.datetime | None = None,
    leadtime: dt.timedelta | None = None,
    key_path: list[YAMLKey] | None = None,
    dry_run: bool = False,
    stdin_ok: bool = False,
) -> dict[str, list[str]]:
    """
    Copy files.

    :param config: YAML-file path, or ``dict`` (read ``stdin`` if missing or ``None``).
    :param target_dir: Path to target directory.
    :param cycle: A datetime object to make available for use in the config.
    :param leadtime: A timedelta object to make available for use in the config.
    :param key_path: Path of keys to config block to use.
    :param dry_run: Do not copy files.
    :param stdin_ok: OK to read from ``stdin``?
    :return: A report on files copied / not copied.
    """
    stager = Copier(
        target_dir=Path(target_dir) if target_dir else None,
        config=_ensure_data_source(config, stdin_ok),
        cycle=cycle,
        leadtime=leadtime,
        key_path=key_path,
    )
    assets = cast(list, stager.go(dry_run=dry_run).assets)
    ready = lambda state: [str(asset.ref) for asset in assets if asset.ready() is state]
    return {STR.ready: ready(True), STR.notready: ready(False)}


def link(
    config: Path | dict | str | None = None,
    target_dir: Path | str | None = None,
    cycle: dt.datetime | None = None,
    hardlink: bool | None = False,
    leadtime: dt.timedelta | None = None,
    key_path: list[YAMLKey] | None = None,
    dry_run: bool = False,
    stdin_ok: bool = False,
    fallback: str | None = None,
) -> dict[str, list[str]]:
    """
    Create links to filesystem items.

    When ``hardlink`` is ``False`` (the default), links may target files, hardlinks, symlinks, and
    directories; when ``True``, links may not be made across filesystems, or to directories. When
    ``fallback`` is set, a copy or symlink will be created, if possible, if a hardlink cannot
    be created.

    :param config: YAML-file path, or ``dict`` (read ``stdin`` if missing or ``None``).
    :param target_dir: Path to target directory.
    :param cycle: A datetime object to make available for use in the config.
    :param hardlink: Create hardlinks instead of symlinks?
    :param leadtime: A timedelta object to make available for use in the config.
    :param key_path: Path of keys to config block to use.
    :param dry_run: Do not link files.
    :param stdin_ok: OK to read from ``stdin``?
    :param fallback: Alternative if hardlink fails (choices: ``copy``, ``symlink``).
    :return: A report on files linked / not linked.
    """
    stager = Linker(
        target_dir=Path(target_dir) if target_dir else None,
        config=_ensure_data_source(config, stdin_ok),
        cycle=cycle,
        hardlink=hardlink,
        leadtime=leadtime,
        key_path=key_path,
        fallback=fallback,
    )
    assets = cast(list, stager.go(dry_run=dry_run).assets)
    ready = lambda state: [str(asset.ref) for asset in assets if asset.ready() is state]
    return {STR.ready: ready(True), STR.notready: ready(False)}


def makedirs(
    config: Path | dict | str | None = None,
    target_dir: Path | str | None = None,
    cycle: dt.datetime | None = None,
    leadtime: dt.timedelta | None = None,
    key_path: list[YAMLKey] | None = None,
    dry_run: bool = False,
    stdin_ok: bool = False,
) -> dict[str, list[str]]:
    """
    Make directories.

    :param config: YAML-file path, or ``dict`` (read ``stdin`` if missing or ``None``).
    :param target_dir: Path to target directory.
    :param cycle: A datetime object to make available for use in the config.
    :param leadtime: A timedelta object to make available for use in the config.
    :param key_path: Path of keys to config block to use.
    :param dry_run: Do not create directories.
    :param stdin_ok: OK to read from ``stdin``?
    :return: A report on directories created / not created.
    """
    stager = MakeDirs(
        target_dir=Path(target_dir) if target_dir else None,
        config=_ensure_data_source(config, stdin_ok),
        cycle=cycle,
        leadtime=leadtime,
        key_path=key_path,
    )
    assets = cast(list, stager.go(dry_run=dry_run).assets)
    ready = lambda state: [str(asset.ref) for asset in assets if asset.ready() is state]
    return {STR.ready: ready(True), STR.notready: ready(False)}


__all__ = ["Copier", "Linker", "MakeDirs", "copy", "link", "makedirs"]
