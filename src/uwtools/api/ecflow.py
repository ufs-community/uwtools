"""
API access to ``uwtools`` ecFlow support.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from uwtools.ecflow import realize as _realize
from uwtools.ecflow import server as _server
from uwtools.ecflow import validate as _validate
from uwtools.utils.api import ensure_data_source as _ensure_data_source
from uwtools.utils.file import str2path as _str2path

if TYPE_CHECKING:
    from pathlib import Path

    from uwtools.config.formats.yaml import YAMLConfig as _YAMLConfig


def realize(
    config: _YAMLConfig | Path | str | None,
    output_path: Path | str | None = None,
    scripts_path: Path | str | None = None,
    stdin_ok: bool = False,
) -> bool:
    """
    Realize the ecFlow workflow defined in the given YAML as a Suite Definition and ecf scripts.

    If no input file is specified, ``stdin`` is read. A ``YAMLConfig`` object may also be provided
    as input. If no output file is specified, the Suite Definition is written to ``stdout``. The ecf
    scripts are not produced if ``scripts_path`` is not provided.

    :param config: YAML input file or ``YAMLConfig`` object (``None`` => read ``stdin``).
    :param output_path: Suite Definition output path (``None`` => write to ``stdout``).
    :param scripts_path: ecf scripts top-level path (``None`` => no scripts are generated).
    :param stdin_ok: OK to read from ``stdin``?
    :raises: ``UWConfigError`` if validation fails.
    :return: ``True``.
    """
    _realize(
        config=_ensure_data_source(_str2path(config), stdin_ok),
        output_path=_str2path(output_path),
        scripts_path=_str2path(scripts_path),
    )
    return True


def server(
    config: Path | None = None,
    port: int | None = None,
    insecure: bool = False,
    report: bool = False,
) -> bool:
    """
    Start an ecFlow server on an available TCP port with SSL security enabled.

    If no port is specified, a random port in the dynamic/private range (49152-65535) is chosen,
    retrying if the port is unavailable. SSL certificates are read from or written to
    ``$HOME/.ecflowrc/ssl``. Use ``insecure`` to skip SSL. Use ``report`` to emit a JSON report
    of the server details (hostname, port) to ``stdout``.

    :param config: Path to UW YAML config file (``None`` => no config file).
    :param port: TCP port to use; overrides config value (``None`` => pick a random available port
        from 49152-65535).
    :param insecure: Start the server without SSL security.
    :param report: Output server details (hostname, port) as JSON to ``stdout``.
    :return: ``True``.
    """
    _server(config=_str2path(config), port=port, insecure=insecure, report=report)
    return True


def validate(
    config: _YAMLConfig | dict | Path | str | None = None,
    stdin_ok: bool = False,
) -> bool:
    """
    Validate an ecFlow config against its schema.

    :param config: YAML input file or ``YAMLConfig`` object to validate (``None`` => read
        ``stdin``).
    :param stdin_ok: OK to read from ``stdin``?
    :return: ``True`` if the config conforms to the schema.
    :raises: ``UWConfigError`` if validation fails.
    """
    return _validate(config=_ensure_data_source(_str2path(config), stdin_ok))
