import os
import re
from abc import ABC, abstractmethod
from collections import UserDict, namedtuple
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
        :param config: Config file to load (None => read from stdin), or initial dict.
        """
        super().__init__()
        if isinstance(config, dict):
            self._config_file = None
            self.update(config)
        else:
            self._config_file = str2path(config) if config else None
            self.data = self._load(self._config_file)
        if self._get_depth_threshold() and self._depth != self._get_depth_threshold():
            raise UWConfigError(
                "Cannot instantiate depth-%s %s with depth-%s config"
                % (self._get_depth_threshold(), type(self).__name__, self._depth)
            )

    def __repr__(self) -> str:
        """
        Return the string representation of a Config object.
        """
        return self._dict_to_str(self.data)

    # Private methods

    def _characterize_values(self, values: dict, parent: str) -> tuple[list, list]:
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
                c, t = self._characterize_values(val, f"{parent}{key}.")
                complete, template = complete + c, template + t
            elif isinstance(val, list):
                for item in val:
                    if isinstance(item, dict):
                        c, t = self._characterize_values(item, parent)
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

    @property
    def _depth(self) -> int:
        """
        The depth of this config's hierarchy.
        """
        return depth(self.data)

    @classmethod
    @abstractmethod
    def _dict_to_str(cls, cfg: dict) -> str:
        """
        Return the string representation of the given dict.

        :param cfg: A dict object.
        """

    @staticmethod
    @abstractmethod
    def _get_depth_threshold() -> Optional[int]:
        """
        Return the config's depth threshold.
        """

    @staticmethod
    @abstractmethod
    def _get_format() -> str:
        """
        Return the config's format name.
        """

    @abstractmethod
    def _load(self, config_file: Optional[Path]) -> dict:
        """
        Read and parse a config file.

        Return the result of loading and parsing the specified config file, or stdin if no file is
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

    def _parse_include(self, ref_dict: Optional[dict] = None) -> None:
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
                self._parse_include(ref_dict[key])
            elif isinstance(value, str):
                if m := re.match(r"^\s*%s\s+(.*)" % INCLUDE_TAG, value):
                    filepaths = yaml.safe_load(m[1])
                    self.update_from(self._load_paths(filepaths))
                    del ref_dict[key]

    # Public methods

    def compare_config(self, dict1: dict, dict2: Optional[dict] = None) -> bool:
        """
        Compare two config dictionaries.

        Assumes a section/key/value structure.

        :param dict1: The first dictionary.
        :param dict2: The second dictionary (default: this config).
        :return: True if the configs are identical, False otherwise.
        """
        dict2 = self.data if dict2 is None else dict2
        diffs2v1: set[tuple] = set()
        diffs1v2: set[tuple] = set()
        missing = namedtuple("missing", [])
        setattr(missing, "__str__", lambda _: "")
        for left, right, diffs in [(dict2, dict1, diffs2v1), (dict1, dict2, diffs1v2)]:
            for sect, items in left.items():
                for key, a in items.items():
                    if (b := right.get(sect, {}).get(key, missing())) != a:
                        diffs.add((sect, key, a, b))
        if lines := sorted(
            (s, k, str(a), type(a).__name__, str(b), type(b).__name__)
            for s, k, a, b in diffs2v1 | {(s, k, b, a) for s, k, a, b in diffs1v2}
        ):
            lines.insert(0, ("Section", "Key", "Value -", "Type -", "Value +", "Type +"))
            widths = [max(len(line[i]) + 1 for line in lines) for i in range(len(lines[0]))]
            dashes: tuple = tuple("-" * w for w in widths)
            for line in [dashes, lines[0], dashes, *lines[1:]]:
                log.info(" ".join(s.ljust(w) for s, w in zip(line, widths)))
            return False
        return True

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
        Dump the config to stdout or a file.

        :param path: Path to dump config to (default: stdout).
        """

    @staticmethod
    @abstractmethod
    def dump_dict(cfg: dict, path: Optional[Path] = None) -> None:
        """
        Dump a provided config dictionary to stdout or a file.

        :param cfg: The in-memory config object to dump.
        :param path: Path to dump config to (default: stdout).
        """

    def update_from(self, src: Union[dict, UserDict]) -> None:
        """
        Update a config.

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

        update(src.data if isinstance(src, UserDict) else src, self.data)
