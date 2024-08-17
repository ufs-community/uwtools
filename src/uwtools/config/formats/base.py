from __future__ import annotations

import os
import re
from abc import ABC, abstractmethod
from collections import UserDict
from copy import deepcopy
from pathlib import Path
from typing import Optional, Union

import yaml

from uwtools.config import jinja2
from uwtools.config.support import INCLUDE_TAG, depth, log_and_error, yaml_to_str
from uwtools.exceptions import UWConfigError
from uwtools.logging import INDENT, log
from uwtools.utils.file import str2path


class Config(ABC, UserDict):
    """
    A base class specifying (and partially implementing) methods to read, manipulate, and write
    several configuration-file formats.
    """

    def __init__(self, config: Optional[Union[dict, str, Path]] = None) -> None:
        """
        Construct a Config object.

        :param config: Config file to load (None => read from stdin), or initial dict.
        """
        super().__init__()
        if isinstance(config, dict):
            self._config_file = None
            self.update(config)
        else:
            self._config_file = str2path(config) if config else None
            self.data = self._load(self._config_file)
        if self.get_depth_threshold() and self.depth != self.get_depth_threshold():
            raise UWConfigError(
                "Cannot instantiate depth-%s %s with depth-%s config"
                % (self.get_depth_threshold(), type(self).__name__, self.depth)
            )

    def __repr__(self) -> str:
        """
        Returns the string representation of a Config object.
        """
        return self._dict_to_str(self.data)

    # Private methods

    @classmethod
    @abstractmethod
    def _dict_to_str(cls, cfg: dict) -> str:
        """
        Returns the string representation of the given dict.

        :param cfg: A dict object.
        """

    @abstractmethod
    def _load(self, config_file: Optional[Path]) -> dict:
        """
        Reads and parses a config file.

        Returns the result of loading and parsing the specified config file, or stdin if no file is
        given.

        :param config_file: Path to config file to load.
        """

    def _load_paths(self, config_files: list[Path]) -> dict:
        """
        Merge and return the contents of a collection of config files.

        :param config_files: Paths to the config files to read and merge.
        """
        cfg = {}
        for config_file in config_files:
            if not os.path.isabs(config_file):
                if self._config_file:
                    config_file = self._config_file.parent / config_file
                else:
                    raise log_and_error(
                        "Reading from stdin, a relative path was encountered: %s" % config_file
                    )
            cfg.update(self._load(config_file=config_file))
        return cfg

    # Public methods

    def characterize_values(self, values: dict, parent: str) -> tuple[list, list]:
        """
        Characterize values as complete or as template placeholders.

        :param values: The dictionary to examine.
        :param parent: Parent key.
        :return: Lists of of complete and template-placeholder values.
        """
        complete: list[str] = []
        template: list[str] = []
        for key, val in values.items():
            if isinstance(val, dict):
                complete.append(f"{INDENT}{parent}{key}")
                c, t = self.characterize_values(val, f"{parent}{key}.")
                complete, template = complete + c, template + t
            elif isinstance(val, list):
                for item in val:
                    if isinstance(item, dict):
                        c, t = self.characterize_values(item, parent)
                        complete, template = complete + c, template + t
                        complete.append(f"{INDENT}{parent}{key}")
                    elif "{{" in str(val) or "{%" in str(val):
                        template.append(f"{INDENT}{parent}{key}: {val}")
                        break
            elif "{{" in str(val) or "{%" in str(val):
                template.append(f"{INDENT}{parent}{key}: {val}")
            else:
                complete.append(f"{INDENT}{parent}{key}")
        return complete, template

    def compare_config(self, dict1: dict, dict2: Optional[dict] = None) -> bool:
        """
        Compare two config dictionaries.

        Assumes a section/key/value structure.

        :param dict1: The first dictionary.
        :param dict2: The second dictionary.
        :return: True if the configs are identical, False otherwise.
        """
        dict2 = self.data if dict2 is None else dict2
        diffs: dict = {}

        for sect, items in dict2.items():
            for key, val in items.items():
                if val != dict1.get(sect, {}).get(key, ""):
                    try:
                        diffs[sect][key] = f" - {val} + {dict1.get(sect, {}).get(key)}"
                    except KeyError:
                        diffs[sect] = {}
                        diffs[sect][key] = f" - {val} + {dict1.get(sect, {}).get(key)}"

        for sect, items in dict1.items():
            for key, val in items.items():
                if val != dict2.get(sect, {}).get(key, "") and diffs.get(sect, {}).get(key) is None:
                    try:
                        diffs[sect][key] = f" - {dict2.get(sect, {}).get(key)} + {val}"
                    except KeyError:
                        diffs[sect] = {}
                        diffs[sect][key] = f" - {dict2.get(sect, {}).get(key)} + {val}"

        for sect, keys in diffs.items():
            for key in keys:
                msg = f"{sect}: {key:>15}: {keys[key]}"
                log.info(msg)

        return not diffs

    @property
    def depth(self) -> int:
        """
        Returns the depth of this config's hierarchy.
        """
        return depth(self.data)

    def dereference(self, context: Optional[dict] = None) -> None:
        """
        Render as much Jinja2 syntax as possible.
        """

        def logstate(state: str) -> None:
            log.debug("Dereferencing, %s value:", state)
            for line in yaml_to_str(self.data).split("\n"):
                log.debug("%s%s", INDENT, line)

        while True:
            logstate("current")
            new = jinja2.dereference(val=self.data, context=context or self.data)
            assert isinstance(new, dict)
            if new == self.data:
                break
            self.data = new
        logstate("final")

    @abstractmethod
    def dump(self, path: Optional[Path]) -> None:
        """
        Dumps the config to stdout or a file.

        :param path: Path to dump config to.
        """

    @staticmethod
    @abstractmethod
    def get_depth_threshold() -> Optional[int]:
        """
        Returns the config's depth threshold.
        """

    @staticmethod
    @abstractmethod
    def dump_dict(cfg: dict, path: Optional[Path] = None) -> None:
        """
        Dumps a provided config dictionary to stdout or a file.

        :param cfg: The in-memory config object to dump.
        :param path: Path to dump config to.
        """

    @staticmethod
    @abstractmethod
    def get_format() -> str:
        """
        Returns the config's format name.
        """

    def parse_include(self, ref_dict: Optional[dict] = None) -> None:
        """
        Recursively process include directives in a config object.

        Recursively traverse the dictionary, replacing include tags with the contents of the files
        they specify. Assumes a section/key/value structure. YAML provides this functionality in its
        own loader.

        :param ref_dict: A config object to process instead of the object's own data.
        """
        if ref_dict is None:
            ref_dict = self.data
        for key, value in deepcopy(ref_dict).items():
            if isinstance(value, dict):
                self.parse_include(ref_dict[key])
            elif isinstance(value, str):
                if m := re.match(r"^\s*%s\s+(.*)" % INCLUDE_TAG, value):
                    filepaths = yaml.safe_load(m[1])
                    self.update_values(self._load_paths(filepaths))
                    del ref_dict[key]

    def update_values(self, src: Union[dict, Config]) -> None:
        """
        Updates a config.

        :param src: The dictionary with new data to use.
        """

        def update(src: dict, dst: dict) -> None:
            for key, val in src.items():
                if isinstance(val, dict):
                    if isinstance(dst.get(key), dict):
                        update(val, dst[key])
                    else:
                        dst[key] = val
                else:
                    dst[key] = val

        update(src.data if isinstance(src, Config) else src, self.data)
