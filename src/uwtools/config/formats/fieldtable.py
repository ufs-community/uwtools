from typing import Optional

from uwtools.config.formats.yaml import YAMLConfig
from uwtools.utils.file import FORMAT, OptionalPath, writable


class FieldTableConfig(YAMLConfig):
    """
    This class exists to write out a field_table format given that its configuration has been set by
    an input YAML file.
    """

    # Public methods

    def dump(self, path: OptionalPath = None) -> None:
        """
        Dumps the config in Field Table format.

        :param path: Path to dump config to.
        """
        self.dump_dict(self.data, path)

    @staticmethod
    def dump_dict(cfg: dict, path: OptionalPath = None) -> None:
        """
        Dumps a provided config dictionary in Field Table format.

        FMS field and tracer managers must be registered in an ASCII table called 'field_table'.
        This table lists field type, target model and methods the querying model will ask for. See
        UFS documentation for more information:

        https://ufs-weather-model.readthedocs.io/en/ufs-v1.0.0/InputsOutputs.html#field-table-file

        The example format for generating a field file is:

        sphum:
          longname: specific humidity
          units: kg/kg
          profile_type:
            name: fixed
            surface_value: 1.e30

        :param cfg: The in-memory config object to dump.
        :param path: Path to dump config to.
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
        with writable(path) as f:
            print("\n".join(lines), file=f)

    @staticmethod
    def get_depth_threshold() -> Optional[int]:
        """
        Returns the config's depth threshold.
        """
        return None

    @staticmethod
    def get_format() -> str:
        """
        Returns the config's format name.
        """
        return FORMAT.fieldtable
