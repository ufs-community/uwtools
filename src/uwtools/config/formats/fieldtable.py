from pathlib import Path
from typing import Optional

from uwtools.config.formats.yaml import YAMLConfig
from uwtools.strings import FORMAT
from uwtools.utils.file import writable


class FieldTableConfig(YAMLConfig):
    """
    This class exists to write out a field_table format given that its configuration has been set by
    an input YAML file.
    """

    # Private methods

    @classmethod
    def _dict_to_str(cls, cfg: dict) -> str:
        """
        Returns the field-table representation of the given dict.

        :param cfg: A dict object.
        """
        lines = []
        for field, settings in cfg.items():
            lines.append(f' "TRACER", "atmos_mod", "{field}"')
            for key, value in settings.items():
                if isinstance(value, dict):
                    method_string = f'{" ":7}"{key}", "{value.pop("name")}"'
                    # All control vars go into one set of quotes.
                    control_vars = [f"{method}={val}" for method, val in value.items()]
                    # Whitespace after the comma matters.
                    lines.append(f'{method_string}, "{", ".join(control_vars)}"')
                else:
                    # Formatting of variable spacing dependent on key length.
                    lines.append(f'{" ":11}"{key}", "{value}"')
            lines[-1] += " /"
        return "\n".join(lines)

    @staticmethod
    def _get_depth_threshold() -> Optional[int]:
        """
        Returns the config's depth threshold.
        """
        return None

    @staticmethod
    def _get_format() -> str:
        """
        Returns the config's format name.
        """
        return FORMAT.fieldtable

    # Public methods

    def dump(self, path: Optional[Path] = None) -> None:
        """
        Dumps the config in Field Table format.

        :param path: Path to dump config to.
        """
        self.dump_dict(self.data, path)

    @classmethod
    def dump_dict(cls, cfg: dict, path: Optional[Path] = None) -> None:
        """
        Dumps a provided config dictionary in Field Table format.

        FMS field and tracer managers must be registered in an ASCII table called ``field_table``.
        This table lists field type, target model and methods the querying model will ask for. See
        UFS documentation for more information:

        https://ufs-weather-model.readthedocs.io/en/ufs-v1.0.0/InputsOutputs.html#field-table-file

        The example format for generating a field file is:

        .. code-block::

           sphum:
             longname: specific humidity
             units: kg/kg
             profile_type:
               name: fixed
               surface_value: 1.e30

        :param cfg: The in-memory config object to dump.
        :param path: Path to dump config to.
        """
        with writable(path) as f:
            print(cls._dict_to_str(cfg), file=f)
