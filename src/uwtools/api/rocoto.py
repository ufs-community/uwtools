import os

from uwtools.rocoto import realize_rocoto_xml as _realize
from uwtools.rocoto import validate_rocoto_xml_file as _validate
from uwtools.types import OptionalPath


def realize(input_file: OptionalPath, output_file: OptionalPath) -> bool:
    """
    ???
    """
    _realize(config=input_file, output_file=output_file)
    return True


def realize_as_str(input_file: OptionalPath) -> str:
    """
    ???
    """
    return _realize(config=input_file, output_file=os.devnull)


def validate(input_file: OptionalPath) -> bool:
    """
    ???
    """
    return _validate(xml_file=input_file)
