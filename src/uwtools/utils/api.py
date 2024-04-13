"""
Support for API modules.
"""

from pathlib import Path
from typing import Any, Optional, Union

from uwtools.config.formats.base import Config
from uwtools.exceptions import UWError


def ensure_config(
    config: Optional[Union[dict, Config, Path, str]] = None, stdin_ok: bool = False
) -> Any:
    """
    Ensure that a config is specified, if required, and is of the right type.

    :param config: Path to config file (read stdin if missing or None).
    :param stdin_ok: OK to read from stdin?
    :return: The config, with a str value converted to a Path.
    :raises: UWError if config is missing and stdin_ok is False.
    """
    if config is None and not stdin_ok:
        raise UWError("Set stdin_ok=True to enable read from stdin")
    return Path(config) if isinstance(config, str) else config
