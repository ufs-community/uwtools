"""
API access to ``uwtools`` Rocoto support.
"""

from pathlib import Path
from typing import Optional, Union

from uwtools.config.formats.yaml import YAMLConfig as _YAMLConfig
from uwtools.rocoto import realize_rocoto_xml as _realize
from uwtools.rocoto import validate_rocoto_xml_file as _validate
from uwtools.utils.api import ensure_data_source as _ensure_data_source
from uwtools.utils.api import str2path as _str2path


def realize(
    config: Optional[Union[_YAMLConfig, Path, str]],
    output_file: Optional[Union[Path, str]] = None,
    stdin_ok: bool = False,
) -> bool:
    """
    Realize the Rocoto workflow defined in the given YAML as XML.

    If no input file is specified, ``stdin`` is read. A ``YAMLConfig`` object may also be provided
    as input. If no output file is specified, ``stdout`` is written to. Both the input config and
    output Rocoto XML will be validated against appropriate schcemas.

    :param config: Path to YAML input file (``None`` or unspecified => read ``stdin``), or
        ``YAMLConfig`` object
    :param output_file: Path to write rendered XML file (``None`` or unspecified => write to
        ``stdout``)
    :param stdin_ok: OK to read from stdin?
    :return: ``True``
    """
    _realize(config=_ensure_data_source(config, stdin_ok), output_file=_str2path(output_file))
    return True


def validate(
    xml_file: Optional[Union[Path, str]] = None,
    stdin_ok: bool = False,
) -> bool:
    """
    Validate purported Rocoto XML file against its schema.

    :param xml_file: Path to XML file (``None`` or unspecified => read ``stdin``)
    :param stdin_ok: OK to read from stdin?
    :return: ``True`` if the XML conforms to the schema, ``False`` otherwise
    """
    return _validate(xml_file=_ensure_data_source(xml_file, stdin_ok))
