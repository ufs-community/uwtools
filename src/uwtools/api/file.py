"""
API access to ``uwtools`` file-management tools.
"""
from pathlib import Path
from typing import List, Optional, Union

from uwtools.file import FileCopier as _FileCopier
from uwtools.file import FileLinker as _FileLinker


def copy(
    target_dir: Path,
    config: Optional[Union[dict, Path]] = None,
    keys: Optional[List[str]] = None,
    dry_run: bool = False,
) -> bool:
    """
    Copy files.

    :param target_dir: Path to target directory
    :param config: YAML-file path, or ``dict`` (read ``stdin`` if missing or ``None``).
    :param keys: YAML keys leading to file dst/src block
    :param dry_run: Do not copy files
    :return: ``True`` if no exception is raised
    """
    _FileCopier(target_dir=target_dir, config=config, keys=keys, dry_run=dry_run).go()
    return True


def link(
    target_dir: Path,
    config: Optional[Union[dict, Path]] = None,
    keys: Optional[List[str]] = None,
    dry_run: bool = False,
) -> bool:
    """
    Link files.

    :param target_dir: Path to target directory
    :param config: YAML-file path, or ``dict`` (read ``stdin`` if missing or ``None``).
    :param keys: YAML keys leading to file dst/src block
    :param dry_run: Do not link files
    :return: ``True`` if no exception is raised
    """
    _FileLinker(target_dir=target_dir, config=config, keys=keys, dry_run=dry_run).go()
    return True
