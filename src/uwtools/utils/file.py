"""
Helpers for working with files and directories.
"""

from __future__ import annotations

import sys
from contextlib import contextmanager
from functools import cache
from importlib import resources
from io import StringIO
from pathlib import Path
from typing import IO, TYPE_CHECKING, Any

from uwtools.logging import log
from uwtools.strings import FORMAT

if TYPE_CHECKING:
    from collections.abc import Generator


class StdinProxy:
    """
    Read stdin once and return its cached data.
    """

    def __init__(self) -> None:
        self._stdin = sys.stdin.read()
        self._reset()

    def __getattr__(self, attr: str) -> Any:
        self._reset()
        return getattr(self._stringio, attr)

    def __iter__(self):
        self._reset()
        yield from self._stringio.read().split("\n")

    def _reset(self) -> None:
        self._stringio = StringIO(self._stdin)


@cache
def _stdinproxy() -> StdinProxy:
    return StdinProxy()


def get_config_format(path: str | Path | None, desc: str | None = None) -> str:
    """
    Return a standardized config format name for a path/filename, defaulting to 'yaml'.

    :param path: A path or filename.
    :param desc: A description of the config.
    :return: One of a set of supported file-format names.
    """
    default = FORMAT.yaml
    if path:
        path = Path(path)
        suffix = path.suffix.replace(".", "")
        return FORMAT.formats().get(suffix, default)
    desc = f"{desc} config" if desc else str(path) if path else "config"
    log.debug("Treating %s as '%s'", desc, default)
    return default


def path_if_it_exists(path: str) -> str:
    """
    Return the given path as an absolute path if it exists, and raises an exception otherwise.

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
    filepath: Path | None = None, mode: str = "r"
) -> Generator[IO | StdinProxy, None, None]:
    """
    If a path to a file is specified, open it and return a readable handle; if not, return readable
    stdin.

    :param filepath: The path to a file to read.
    """
    if filepath:
        with Path(filepath).open(mode) as f:
            yield f
    else:
        yield _stdinproxy()


def resource_path(suffix: str = "") -> Path:
    """
    Return a pathlib Path object to a uwtools resource file.

    :param suffix: A subpath relative to the location of the uwtools resource files. The prefix path
        to the resources files is known to Python and varies based on installation location.
    """
    with resources.as_file(resources.files("uwtools.resources")) as prefix:
        return prefix / suffix


def str2path(val: Any) -> Any:
    """
    Return str value as Path, other types unmodified.

    :param val: Any value.
    """
    return Path(val) if isinstance(val, str) else val


@contextmanager
def writable(filepath: Path | None = None, mode: str = "w") -> Generator[IO, None, None]:
    """
    If a path to a file is specified, open it and return a writable handle; if not, return writeable
    stdout.

    :param filepath: The path to a file to write to.
    """
    if filepath:
        filepath.parent.mkdir(parents=True, exist_ok=True)
        with filepath.open(mode) as f:
            yield f
    else:
        yield sys.stdout
