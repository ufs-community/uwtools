"""
Helpers for working with files and directories.
"""

import sys
from contextlib import contextmanager
from dataclasses import dataclass, fields
from datetime import datetime as dt
from functools import cache
from importlib import resources
from io import StringIO
from pathlib import Path
from typing import IO, Any, Dict, Generator, List, Union

from uwtools.exceptions import UWError
from uwtools.logging import log


@dataclass(frozen=True)
class FORMAT:
    """
    A mapping from config format names to literal strings.
    """

    # Canonical strings:

    _atparse: str = "atparse"
    _fieldtable: str = "fieldtable"
    _ini: str = "ini"
    _jinja2: str = "jinja2"
    _nml: str = "nml"
    _sh: str = "sh"
    _xml: str = "xml"
    _yaml: str = "yaml"

    # Variants:

    atparse: str = _atparse
    bash: str = _sh
    cfg: str = _ini
    fieldtable: str = _fieldtable
    ini: str = _ini
    jinja2: str = _jinja2
    nml: str = _nml
    sh: str = _sh
    yaml: str = _yaml
    yml: str = _yaml

    @staticmethod
    def extensions() -> List[str]:
        """
        Returns recognized filename extensions.
        """
        return [FORMAT.ini, FORMAT.nml, FORMAT.sh, FORMAT.yaml]

    @staticmethod
    def formats() -> Dict[str, str]:
        """
        Returns the recognized format names.
        """
        return {
            field.name: str(getattr(FORMAT, field.name))
            for field in fields(FORMAT)
            if not field.name.startswith("_")
        }


class StdinProxy:
    """
    Reads stdin once but permits multiple reads of its data.
    """

    def __init__(self) -> None:
        self._stdin = sys.stdin.read()
        self._reset()

    def __getattr__(self, attr: str) -> Any:
        self._reset()
        return getattr(self._stringio, attr)

    def __iter__(self):
        self._reset()
        for line in self._stringio.read().split("\n"):
            yield line

    def _reset(self) -> None:
        self._stringio = StringIO(self._stdin)


@cache
def _stdinproxy():
    return StdinProxy()


def get_file_format(path: Path) -> str:
    """
    Returns a standardized file format name given a path/filename.

    :param path: A path or filename.
    :return: One of a set of supported file-format names.
    :raises: ValueError if the path/filename suffix is unrecognized.
    """
    suffix = Path(path).suffix.replace(".", "")
    try:
        return FORMAT.formats()[suffix]
    except KeyError as e:
        msg = f"Cannot deduce format of '{path}' from unknown extension '{suffix}'"
        log.critical(msg)
        raise UWError(msg) from e


def path_if_it_exists(path: str) -> str:
    """
    Returns the given path as an absolute path if it exists, and raises an exception otherwise.

    :param path: The filesystem path to test.
    :return: The same filesystem path as an absolute path.
    :raises: FileNotFoundError is path does not exst
    """
    p = Path(path)
    if not p.exists():
        msg = f"{path} does not exist"
        print(msg, file=sys.stderr)
        raise FileNotFoundError(msg)
    return str(p.absolute())


@contextmanager
def readable(
    filepath: Optional[Path] = None, mode: str = "r"
) -> Generator[Union[IO, StdinProxy], None, None]:
    """
    If a path to a file is specified, open it and return a readable handle; if not, return readable
    stdin.

    :param filepath: The path to a file to read.
    """
    if filepath:
        with open(filepath, mode, encoding="utf-8") as f:
            yield f
    else:
        yield _stdinproxy()


def resource_pathobj(suffix: str = "") -> Path:
    """
    Returns a pathlib Path object to a uwtools resource file.

    :param suffix: A subpath relative to the location of the uwtools resource files. The prefix path
        to the resources files is known to Python and varies based on installation location.
    """
    with resources.as_file(resources.files("uwtools.resources")) as prefix:
        return prefix / suffix


def validate_existing_action(exist_act: str, valid_actions: List[str]) -> None:
    """
    Ensure that action specified for an existing directory is valid.

    :param exist_act: Action to check.
    :param valid_actions: Actions valid for the caller's context.
    :raises: ValueError if specified action is invalid.
    """
    if exist_act not in valid_actions:
        raise ValueError(
            'Specify one of %s as exist_act, not "%s"'
            % (", ".join(f'"{x}"' for x in valid_actions), exist_act)
        )


@contextmanager
def writable(filepath: Optional[Path] = None, mode: str = "w") -> Generator[IO, None, None]:
    """
    If a path to a file is specified, open it and return a writable handle; if not, return writeable
    stdout.

    :param filepath: The path to a file to write to.
    """
    if filepath:
        with open(filepath, mode, encoding="utf-8") as f:
            yield f
    else:
        yield sys.stdout
