"""
API access to uwtools file-management tools.
"""
from pathlib import Path
from typing import List, Optional

from uwtools.file import FileCopier as _FileCopier
from uwtools.file import FileLinker as _FileLinker


def copy(
    target_dir: Path,
    config_file: Optional[Path] = None,
    keys: Optional[List[str]] = None,
    dry_run: bool = False,
) -> bool:
    """
    Copy files.

    :param target_dir: Path to target directory
    :param config_file: Path to YAML config file (defaults to stdin)
    :param keys: YAML keys leading to file dst/src block
    :param dry_run: Do not copy files
    :return: True if no exception is raised
    """
    _FileCopier(target_dir=target_dir, config_file=config_file, keys=keys, dry_run=dry_run).go()
    return True


def link(
    target_dir: Path,
    config_file: Optional[Path] = None,
    keys: Optional[List[str]] = None,
    dry_run: bool = False,
) -> bool:
    """
    Link files.

    :param target_dir: Path to target directory
    :param config_file: Path to YAML config file (defaults to stdin)
    :param keys: YAML keys leading to file dst/src block
    :param dry_run: Do not link files
    :return: True if no exception is raised
    """
    _FileLinker(target_dir=target_dir, config_file=config_file, keys=keys, dry_run=dry_run).go()
    return True
