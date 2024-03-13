"""
File handling.
"""
from pathlib import Path
from typing import List, Optional

from uwtools.config.formats.yaml import YAMLConfig


class FileHandler:
    """
    The base class for file handlers.
    """

    def __init__(
        self,
        target_dir: Path,
        config_file: Optional[Path],
        keys: Optional[List[str]] = None,
        dry_run: bool = False,
    ) -> None:
        """
        Handle files.

        :param target_dir: Path to target directory
        :param config_file: Path to YAML config file (defaults to stdin)
        :param keys: YAML keys leading to file dst/src block
        :param dry_run: Do not copy files
        """
        self._target_dir = target_dir
        self._config = YAMLConfig(config=config_file)
        self._keys = keys
        self._dry_run = dry_run
        self._config.dereference()
        self._validate()

    def _validate(self) -> None:
        """
        Validate config against its schema.
        """


class FileCopier(FileHandler):
    """
    PM WRIRTEME.
    """


class FileLinker(FileHandler):
    """
    PM WRITEME.
    """
