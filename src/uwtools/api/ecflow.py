"""
API access to ``uwtools`` ecFlow support.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from uwtools.ecflow import realize as _realize
from uwtools.ecflow import validate_file as _validate
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
    as input. If no output file is specified, the Suite Definition is written to``stdout``. The ecf
    scripts are not produced if scripts_path is not provided.

    :param config: YAML input file or ``YAMLConfig`` object (``None`` => read ``stdin``).
    :param output_path: Suite Definition output path (``None`` => write to ``stdout``).
    :param scripts_path: ecf scripts top-level path (``None`` => no scripts are generated).
    :param stdin_ok: OK to read from ``stdin``?
    :return: ``True``.
    """
    _realize(
        config=_ensure_data_source(_str2path(config), stdin_ok),
        output_path=_str2path(output_path),
        scripts_path=_str2path(scripts_path),
    )
    return True


def validate(
    yaml_file: Path | str | None = None,
    stdin_ok: bool = False,
) -> bool:
    """
    Validate the input YAML against its schema.

    :param yaml_file: Path to YAML file (``None`` or unspecified => read ``stdin``).
    :param stdin_ok: OK to read from ``stdin``?
    :return: ``True`` if the YAML conforms to the schema, ``False`` otherwise.
    """
    return _validate(yaml_file=_ensure_data_source(_str2path(yaml_file), stdin_ok))
