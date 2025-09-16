from __future__ import annotations

import difflib
import re
from abc import ABC, abstractmethod
from collections import UserDict
from copy import deepcopy
from io import StringIO
from pathlib import Path
from typing import Any, cast

import yaml

from uwtools.config import jinja2
from uwtools.config.support import (
    INCLUDE_TAG,
    UWYAMLConvert,
    depth,
    dict_to_yaml_str,
    log_and_error,
)
from uwtools.exceptions import UWConfigError
from uwtools.logging import INDENT, MSGWIDTH, log
from uwtools.utils.file import str2path


class Config(ABC, UserDict):
    """
    A base class specifying (and partially implementing) methods to read, manipulate, and write
    several configuration-file formats.
    """

    def __init__(self, config: dict | str | Config | Path | None = None) -> None:
        """
        :param config: Config file to load (None => read from stdin), or initial dict.
        """
        super().__init__()
        if isinstance(config, dict):
            self._config_file = None
            self.update(deepcopy(config))
        elif isinstance(config, Config):
            self._config_file = config._config_file  # noqa: SLF001
            self.update(deepcopy(config.data))
        else:
            self._config_file = str2path(config) if config else None
            self.data = self._load(self._config_file)
        if self._get_depth_threshold() and self._depth != self._get_depth_threshold():
            msg = "Cannot instantiate depth-%s %s with depth-%s config" % (
                self._get_depth_threshold(),
                type(self).__name__,
                self._depth,
            )
            raise UWConfigError(msg)

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

        def jinja2val(val: Any) -> str | None:
            try:
                s = str(val)
            except ValueError:
                assert isinstance(val, UWYAMLConvert)
                s = val.tagged_string
            return s if "{{" in s or "{%" in s else None

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
                    elif val := jinja2val(val):
                        template.append(f"{INDENT}{parent}{key}: {val}")
                        break
            elif val := jinja2val(val):
                template.append(f"{INDENT}{parent}{key}: {val}")
            else:
                complete.append(f"{INDENT}{parent}{key}")
        return complete, template

    @staticmethod
    def _compare_config_get_lines(d: dict) -> list[str]:
        """
        Returns a line-by-line YAML representation of the given dict.

        :param d: A dict object.
        """
        sio = StringIO()
        sio.write(dict_to_yaml_str(d, sort=True))
        return sio.getvalue().splitlines(keepends=False)

    @staticmethod
    def _compare_config_log_header() -> None:
        """
        Log a visual header and description of diff markers.
        """
        log.info("-" * MSGWIDTH)
        log.info("↓ ? = info | -/+ = line unique to - or + file | blank = matching line")
        log.info("-" * MSGWIDTH)

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
    def _get_depth_threshold() -> int | None:
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
    def _load(self, config_file: Path | None) -> dict:
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
            cf = config_file
            if not Path(cf).is_absolute():
                if self._config_file:
                    cf = self._config_file.parent / config_file
                else:
                    raise log_and_error(
                        "Reading from stdin, a relative path was encountered: %s" % cf
                    )
            cfg.update(self._load(config_file=cf))
        return cfg

    def _parse_include(self, ref_dict: dict | None = None) -> None:
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
            elif isinstance(value, str) and (m := re.match(r"^\s*%s\s+(.*)" % INCLUDE_TAG, value)):
                filepaths = yaml.safe_load(m[1])
                self.update_from(self._load_paths(filepaths))
                del ref_dict[key]

    # Public methods

    @abstractmethod
    def as_dict(self) -> dict:
        """
        Returns a pure dict version of the config.
        """

    def compare_config(
        self, dict1: dict, dict2: dict | None = None, header: bool | None = True
    ) -> bool:
        """
        Compare two config dictionaries.

        Assumes a section/key/value structure.

        :param dict1: The first dictionary.
        :param dict2: The second dictionary (default: this config).
        :return: True if the configs are identical, False otherwise.
        """
        dict2 = self.as_dict() if dict2 is None else dict2
        lines1, lines2 = map(self._compare_config_get_lines, [dict1, dict2])
        difflines = list(difflib.ndiff(lines2, lines1))
        if all(line[0] == " " for line in difflines):  # i.e. no +/-/? lines
            return True
        if header:
            self._compare_config_log_header()
        for diffline in difflines:
            log.info(diffline.rstrip())
        return False

    @property
    def config_file(self) -> Path | None:
        """
        Return the path to the config file from which this object was instantiated, if applicable.
        """
        return self._config_file

    def dereference(self, context: dict | None = None) -> Config:
        """
        Render as much Jinja2 syntax as possible.
        """

        def logstate(state: str) -> None:
            jinja2.deref_debug("Dereferencing, %s value:" % state)
            for line in dict_to_yaml_str(self.data).split("\n"):
                jinja2.deref_debug("%s%s" % (INDENT, line))

        # Context object 'ctx', from which Jinja2 will try to retrieve values for rendering template
        # expressions found in config keys and values, starts as a deep copy of the current config,
        # so that self-references can be dereferenced. It is structurally updated from a deep copy,
        # performed in update_from(), of the optional 'context' object, to provide additional and/or
        # overriding values. Deep copies are used to avoid sturctural sharing between 'ctx' and its
        # precursors.
        #
        # During each iteration of the loop, which terminates when a fixed point is found (i.e. no
        # more template expressions can be rendered), `ctx` is updated to replace unrendered values
        # with newly rendered ones, so that they can be used to render yet more values in the next
        # iteration.

        ctx = deepcopy(self)
        ctx.update_from(context or {})
        while True:
            logstate("current")
            new = jinja2.dereference(val=self.data, context=cast(dict, ctx))
            assert isinstance(new, dict)
            if new == self.data:
                break
            ctx.update_from(new)
            self.data = new
        logstate("final")
        return self

    @abstractmethod
    def dump(self, path: Path | None) -> None:
        """
        Dump the config to stdout or a file.

        :param path: Path to dump config to (default: stdout).
        """

    @staticmethod
    @abstractmethod
    def dump_dict(cfg: dict, path: Path | None = None) -> None:
        """
        Dump a provided config dictionary to stdout or a file.

        :param cfg: The in-memory config object to dump.
        :param path: Path to dump config to (default: stdout).
        """

    def update_from(self, src: dict | UserDict) -> None:
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

        update(deepcopy(src.data if isinstance(src, UserDict) else src), self.data)
