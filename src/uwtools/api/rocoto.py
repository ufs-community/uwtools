import uwtools.rocoto
from uwtools.types import OptionalPath


def realize(input_file: OptionalPath, output_file: OptionalPath) -> bool:
    """
    ???
    """
    return uwtools.rocoto.realize_rocoto_xml(config_file=input_file, output_file=output_file)


def validate(input_file: OptionalPath) -> bool:
    """
    ???
    """
    return uwtools.rocoto.validate_rocoto_xml(input_xml=input_file)
