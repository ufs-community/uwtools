"""
API access to ``uwtools`` file-management tools.
"""

from pathlib import Path
from typing import List, Optional, Union

from uwtools.exceptions import UWError
from uwtools.file import FileCopier as _FileCopier
from uwtools.file import FileLinker as _FileLinker


def copy(
    target_dir: Union[Path, str],
    config: Optional[Union[dict, Path, str]] = None,
    keys: Optional[List[str]] = None,
    dry_run: bool = False,
    stdin_ok: bool = False,
) -> bool:
    """
    Copy files.

    :param target_dir: Path to target directory
    :param config: YAML-file path, or ``dict`` (read ``stdin`` if missing or ``None``).
    :param keys: YAML keys leading to file dst/src block
    :param dry_run: Do not copy files
    :param stdin_ok: OK to read config from stdin?
    :return: ``True`` if no exception is raised
    """
    if config is None and not stdin_ok:
        raise UWError("Set stdin_ok=True to enable read from stdin")
    config = Path(config) if isinstance(config, str) else config
    _FileCopier(target_dir=Path(target_dir), config=config, keys=keys, dry_run=dry_run).go()
    return True


def link(
    target_dir: Union[Path, str],
    config: Optional[Union[dict, Path, str]] = None,
    keys: Optional[List[str]] = None,
    dry_run: bool = False,
    stdin_ok: bool = False,
) -> bool:
    """
    Link files.

    :param target_dir: Path to target directory
    :param config: YAML-file path, or ``dict`` (read ``stdin`` if missing or ``None``).
    :param keys: YAML keys leading to file dst/src block
    :param dry_run: Do not link files
    :param stdin_ok: OK to read config from stdin?
    :return: ``True`` if no exception is raised
    """
    if config is None and not stdin_ok:
        raise UWError("Set stdin_ok=True to enable read from stdin")
    config = Path(config) if isinstance(config, str) else config
    _FileLinker(target_dir=Path(target_dir), config=config, keys=keys, dry_run=dry_run).go()
    return True
