import os
from typing import Optional, Union

from uwtools.config.atparse_to_jinja2 import convert as _convert_atparse_to_jinja2
from uwtools.config.formats.fieldtable import FieldTableConfig as _FieldTableConfig
from uwtools.config.formats.ini import INIConfig as _INIConfig
from uwtools.config.formats.nml import NMLConfig as _NMLConfig
from uwtools.config.formats.sh import SHConfig as _SHConfig
from uwtools.config.formats.yaml import Config as _Config
from uwtools.config.formats.yaml import YAMLConfig as _YAMLConfig
from uwtools.config.tools import compare_configs as _compare
from uwtools.config.tools import realize_config as _realize
from uwtools.config.validator import validate_yaml as _validate_yaml
from uwtools.types import DefinitePath, OptionalPath
from uwtools.utils.file import FORMAT as _FORMAT

# Public


def compare(
    config_a_path: DefinitePath,
    config_a_format: str,
    config_b_path: DefinitePath,
    config_b_format: str,
) -> bool:
    """
    Compare two config files.

    :param config_a_path: Path to first config file.
    :param config_a_format: Format of first config file.
    :param config_b_path: Path to second config file.
    :param config_b_format: Format of second config file.
    :return: ``False`` if config files had differences, otherwise ``True``.
    """
    return _compare(
        config_a_path=config_a_path,
        config_a_format=config_a_format,
        config_b_path=config_b_path,
        config_b_format=config_b_format,
    )


def get_fieldtable_config(config: Union[dict, OptionalPath] = None) -> _FieldTableConfig:
    """
    Get a ``FieldTableConfig`` object.

    :param config: Config file to load (``None`` => read ``stdin``), or initial ``dict``.
    :return: An initialized ``FieldTableConfig`` object.
    """
    return _FieldTableConfig(config=config)


def get_ini_config(config: Union[dict, OptionalPath] = None) -> _INIConfig:
    """
    Get an ``INIConfig`` object.

    :param config: Config file to load (``None`` => read ``stdin``), or initial ``dict``.
    :return: An initialized ``INIConfig`` object.
    """
    return _INIConfig(config=config)


def get_nml_config(config: Union[dict, OptionalPath] = None) -> _NMLConfig:
    """
    Get an ``NMLConfig`` object.

    :param config: Config file to load (``None`` => read ``stdin``), or initial ``dict``.
    :return: An initialized ``NMLConfig`` object.
    """
    return _NMLConfig(config=config)


def get_sh_config(config: Union[dict, OptionalPath] = None) -> _SHConfig:
    """
    Get an ``SHConfig`` object.

    :param config: Config file to load (``None`` => read ``stdin``), or initial ``dict``.
    :return: An initialized ``SHConfig`` object.
    """
    return _SHConfig(config=config)


def get_yaml_config(config: Union[dict, OptionalPath] = None) -> _YAMLConfig:
    """
    Get a ``YAMLConfig`` object.

    :param config: Config file to load (``None`` => read ``stdin``), or initial ``dict``.
    :return: An initialized ``YAMLConfig`` object.
    """
    return _YAMLConfig(config=config)


def realize(
    input_config: Union[dict, _Config, OptionalPath] = None,
    input_format: Optional[str] = None,
    output_file: OptionalPath = None,
    output_format: Optional[str] = None,
    values: Union[dict, _Config, OptionalPath] = None,
    values_format: Optional[str] = None,
    values_needed: bool = False,
    dry_run: bool = False,
) -> bool:
    """
    Realize an output config based on an input config and an optional values-providing config.

    If no input is specified, ``stdin`` is read. If no output is specified, ``stdout`` is written to.

    When a filename is available for an input or output, its format will be deduced from its extension, if possible. This can be overriden by specifying the format explicitly, and it is required to do so for reads from ``stdin`` or writes to ``stdout``, as no attempt is made to deduce the format of streamed data.

    A ``dict`` may also be provided as an input value.

    If ``values_needed`` is ``True``, a report of values needed to realize the config is logged.

    In ``dry_run`` mode, output is written to ``stderr``.

    :param input_config: Input config file (``None`` => read ``stdin``).
    :param input_format: Format of the input config.
    :param output_file: Output config file (``None`` => write to ``stdout``).
    :param output_format: Format of the output config.
    :param values: Source of values used to modify input.
    :param values_format: Format of values when sourced from file.
    :param values_needed: Report complete, missing, and template values.
    :param dry_run: Log output instead of writing to output.
    :return: ``True``.
    """
    _realize(
        input_config=_ensure_config_arg_type(input_config),
        input_format=input_format,
        output_file=output_file,
        output_format=output_format,
        values=_ensure_config_arg_type(values),
        values_format=values_format,
        values_needed=values_needed,
        dry_run=dry_run,
    )
    return True


def realize_to_dict(
    input_config: Union[dict, _Config, OptionalPath] = None,
    input_format: Optional[str] = None,
    values: Union[dict, _Config, OptionalPath] = None,
    values_format: Optional[str] = None,
    values_needed: bool = False,
    dry_run: bool = False,
) -> dict:
    """
    Realize an output config based on an input config and an optional values-providing config.

    If no input is specified, ``stdin`` is read.

    When a filename is available for an input, its format will be deduced from its extension, if possible. This can be overriden by specifying the format explicitly, and it is required to do so for reads from ``stdin``, as no attempt is made to deduce the format of streamed data.

    A ``dict`` may also be provided as an input value.

    If ``values_needed`` is ``True``, a report of values needed to realize the config is logged.

    In ``dry_run`` mode, output is written to ``stderr``.

    :param input_config: Input config file (``None`` => read ``stdin``).
    :param input_format: Format of the input config.
    :param values: Source of values used to modify input.
    :param values_format: Format of values when sourced from file.
    :param values_needed: Report complete, missing, and template values.
    :param dry_run: Log output instead of writing to output.
    :return: A ``dict`` representing the realized config.
    """
    return _realize(
        input_config=_ensure_config_arg_type(input_config),
        input_format=input_format,
        output_file=os.devnull,
        output_format=None,
        values=_ensure_config_arg_type(values),
        values_format=values_format,
        values_needed=values_needed,
        dry_run=dry_run,
    )


def translate(
    input_format: str,
    output_format: str,
    input_file: OptionalPath = None,
    output_file: OptionalPath = None,
    dry_run: bool = False,
) -> bool:
    """
    Translate a config to a different format.

    Currently supports atparse -> Jinja2 translation, in which ``@[]`` tokens are replaced with Jinja2 ``{{}}`` equivalents. Specify ``input_format=atparse`` and ``output_format=jinja2``.

    If no input file is specified, ``stdin`` is read. If no output file is specified, ``stdout`` is written to. In ``dry_run mode``, output is written to ``stderr``.

    :param input_file: Path to the template containing atparse syntax.
    :param output_file: Path to the file to write the converted template to.
    :param dry_run: Run in dry-run mode?
    :return: ``True`` if translation was successful, ``False`` otherwise.
    """
    if input_format == _FORMAT.atparse and output_format == _FORMAT.jinja2:
        _convert_atparse_to_jinja2(input_file=input_file, output_file=output_file, dry_run=dry_run)
        return True
    return False


def validate(
    schema_file: DefinitePath, config: Optional[Union[dict, _YAMLConfig, OptionalPath]] = None
) -> bool:
    """
    Check whether the specified config conforms to the specified JSON Schema spec.

    If no config is specified, ``stdin`` is read and will be parsed as YAML and then validated. A ``dict`` or a ``YAMLConfig`` instance may also be provided for validation.

    :param schema_file: The JSON Schema file to use for validation.
    :param config: The config to validate.
    :return: ``True`` if the YAML file conforms to the schema, ``False`` otherwise.
    """
    return _validate_yaml(schema_file=schema_file, config=config)


# Private


def _ensure_config_arg_type(
    config: Union[dict, _Config, OptionalPath]
) -> Union[_Config, OptionalPath]:
    """
    Encapsulate a dict in a Config; return a Config or path argument as-is.

    :param config: A config as a dict, Config, or path.
    """
    if isinstance(config, dict):
        return _YAMLConfig(config=config)
    return config
