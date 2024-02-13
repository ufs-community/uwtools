from typing import Union

from uwtools.config.formats.yaml import YAMLConfig
from uwtools.rocoto import realize_rocoto_xml as _realize
from uwtools.rocoto import validate_rocoto_xml_file as _validate
from uwtools.types import Optional[Path]


def realize(config: Union[YAMLConfig, Optional[Path]], output_file: Optional[Path] = None) -> bool:
    """
    Realize the Rocoto workflow defined in the given YAML as XML.

    If no input file is specified, ``stdin`` is read. A ``YAMLConfig`` object may also be provided
    as input. If no output file is specified, ``stdout`` is written to. Both the input config and
    output Rocoto XML will be validated against appropriate schcemas.

    :param config: Path to YAML input file (``None`` or unspecified => read ``stdin``), or
        ``YAMLConfig`` object
    :param output_file: Path to write rendered XML file (``None`` or unspecified => write to
        ``stdout``)
    :return: ``True``
    """
    _realize(config=config, output_file=output_file)
    return True


def validate(xml_file: Optional[Path] = None) -> bool:
    """
    Validate purported Rocoto XML file against its schema.

    :param xml_file: Path to XML file (``None`` or unspecified => read ``stdin``)
    :return: ``True`` if the XML conforms to the schema, ``False`` otherwise
    """
    return _validate(xml_file=xml_file)
