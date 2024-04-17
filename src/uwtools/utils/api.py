"""
Support for API modules.
"""

from pathlib import Path
from typing import Any, Optional, Union

from uwtools.config.formats.base import Config
from uwtools.exceptions import UWError


def ensure_data_source(
    data_source: Optional[Union[dict, Config, Path, str]], stdin_ok: bool
) -> Any:
    """
    If stdin read is disabled, ensure that a data source was provided. Convert str -> Path.

    :param data_source: Data source as provided to API.
    :param stdin_ok: OK to read from stdin?
    :return: Data source, with a str converted to Path.
    :raises: UWError if no data source was provided and stdin read is disabled.
    """
    if data_source is None and not stdin_ok:
        raise UWError("Set stdin_ok=True to permit read from stdin")
    return str2path(data_source)


def str2path(val: Any) -> Any:
    """
    Return str value as Path, other types unmodified.

    :param val: Any value.
    """
    return Path(val) if isinstance(val, str) else val
