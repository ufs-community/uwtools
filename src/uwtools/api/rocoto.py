from uwtools.rocoto import realize_rocoto_xml as _realize
from uwtools.rocoto import validate_rocoto_xml_file as _validate
from uwtools.types import OptionalPath


def realize(input_file: OptionalPath = None, output_file: OptionalPath = None) -> bool:
    """
    ???
    """
    _realize(config=input_file, output_file=output_file)
    return True


def validate(input_file: OptionalPath = None) -> bool:
    """
    ???
    """
    return _validate(xml_file=input_file)
