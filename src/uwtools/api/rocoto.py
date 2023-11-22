from uwtools.rocoto import realize_rocoto_xml as _realize
from uwtools.rocoto import validate_rocoto_xml as _validate
from uwtools.types import OptionalPath


def realize(input_file: OptionalPath, output_file: OptionalPath) -> bool:
    """
    ???
    """
    return _realize(config_file=input_file, output_file=output_file)


def validate(input_file: OptionalPath) -> bool:
    """
    ???
    """
    return _validate(input_xml=input_file)
