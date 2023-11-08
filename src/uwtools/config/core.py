"""
Core classes and functions for working with configs.
"""

from __future__ import annotations

import configparser
import copy
import json
import os
import re
from abc import ABC, abstractmethod
from collections import OrderedDict, UserDict
from types import SimpleNamespace as ns
from typing import Dict, List, Optional, Tuple, Type, Union

import f90nml
import jinja2
import yaml

from uwtools.exceptions import UWConfigError
from uwtools.logging import MSGWIDTH, log
from uwtools.types import DefinitePath, OptionalPath
from uwtools.utils.file import FORMAT, get_file_type, readable, writable

_INCLUDE_TAG = "!INCLUDE"

_MSGS = ns(
    unhashable="""
ERROR:
The input config file may contain a Jinja2 templated value at the location listed above. Ensure the
value is enclosed in quotes.
""".strip(),
    unregistered_constructor="""
ERROR:
The input config file contains a constructor that is not registered with the uwtools package.

constructor: {constructor}
config file: {config_file}

Define the constructor before proceeding.
""".strip(),
    unregistered_filter="""
ERROR:
The input config file contains a Jinja2 filter that is not registered with the uwtools package.

filter: {filter}
key: {key}

Define the filter before proceeding.
""".strip(),
)

_YAMLVal = Union[bool, dict, float, int, list, str]


class Config(ABC, UserDict):
    """
    A base class specifying (and partially implementing) methods to read, manipulate, and write
    several configuration-file formats.
    """

    def __init__(self, config_file: OptionalPath = None) -> None:
        """
        Construct a Config object.

        :param config_file: Path to the config file to load.
        """
        super().__init__()
        self._config_file = str(config_file) if config_file else None
        self.update(self._load(self._config_file))

    def __repr__(self) -> str:
        """
        The string representation of a Config object.
        """
        return json.dumps(self.data)

    # Private methods

    @abstractmethod
    def _load(self, config_file: OptionalPath) -> dict:
        """
        Reads and parses a config file.

        Returns the result of loading and parsing the specified config file, or stdin if no file is
        given.

        :param config_file: Path to config file to load.
        """

    def _load_paths(self, config_files: List[str]) -> dict:
        """
        Merge and return the contents of a collection of config files.

        :param config_files: Paths to the config files to read and merge.
        """
        cfg = {}
        for config_file in config_files:
            if not os.path.isabs(config_file):
                if self._config_file:
                    config_file = os.path.join(os.path.dirname(self._config_file), config_file)
                else:
                    raise _log_and_error(
                        "Reading from stdin, a relative path was encountered: %s" % config_file
                    )
            cfg.update(self._load(config_file=config_file))
        return cfg

    # Public methods

    def characterize_values(self, values: dict, parent: str) -> Tuple[list, list, list]:
        """
        Characterize values as complete, empty, or template placeholders.

        :param values: The dictionary to examine.
        :param parent: Parent key.
        """
        complete: List[str] = []
        empty: List[str] = []
        template: List[str] = []
        for key, val in values.items():
            if isinstance(val, dict):
                complete.append(f"    {parent}{key}")
                c, e, t = self.characterize_values(val, f"{parent}{key}.")
                complete, empty, template = complete + c, empty + e, template + t
            elif isinstance(val, list):
                for item in val:
                    if isinstance(item, dict):
                        c, e, t = self.characterize_values(item, parent)
                        complete, empty, template = complete + c, empty + e, template + t
                        complete.append(f"    {parent}{key}")
                    elif "{{" in str(val) or "{%" in str(val):
                        template.append(f"    {parent}{key}: {val}")
                        break
            elif "{{" in str(val) or "{%" in str(val):
                template.append(f"    {parent}{key}: {val}")
            elif val == "" or val is None:
                empty.append(f"    {parent}{key}")
            else:
                complete.append(f"    {parent}{key}")
        return complete, empty, template

    def compare_config(self, dict1: dict, dict2: Optional[dict] = None) -> bool:
        """
        Compare two config dictionaries.

        Assumes a section/key/value structure.

        :param dict1: The first dictionary.
        :param dict2: The second dictionary.
        """
        dict2 = self.data if dict2 is None else dict2
        diffs: dict = {}

        for sect, items in dict2.items():
            for key, val in items.items():
                if val != dict1.get(sect, {}).get(key, ""):
                    try:
                        diffs[sect][key] = f" - {val} + {dict1.get(sect, {}).get(key)}"
                    except KeyError:
                        diffs[sect] = {}
                        diffs[sect][key] = f" - {val} + {dict1.get(sect, {}).get(key)}"

        for sect, items in dict1.items():
            for key, val in items.items():
                if val != dict2.get(sect, {}).get(key, "") and diffs.get(sect, {}).get(key) is None:
                    try:
                        diffs[sect][key] = f" - {dict2.get(sect, {}).get(key)} + {val}"
                    except KeyError:
                        diffs[sect] = {}
                        diffs[sect][key] = f" - {dict2.get(sect, {}).get(key)} + {val}"

        for sect, keys in diffs.items():
            for key in keys:
                msg = f"{sect}: {key:>15}: {keys[key]}"
                log.info(msg)

        return not diffs

    @property
    def depth(self) -> int:
        """
        The depth of this config's hierarchy.
        """
        return self._depth(self.data)

    def dereference_all(self) -> None:
        """
        Dereference iteratively until no Jinja2 templates remain.
        """
        while True:
            new = _dereference(val=self.data, context={**os.environ, **self.data})
            if new == self.data:
                break
            assert isinstance(new, dict)
            self.data = new

    @abstractmethod
    def dump(self, path: OptionalPath) -> None:
        """
        Dumps the config to stdout or a file.

        :param path: Path to dump config to.
        """

    @staticmethod
    @abstractmethod
    def dump_dict(path: OptionalPath, cfg: dict, opts: Optional[ns] = None) -> None:
        """
        Dumps a provided config dictionary to stdout or a file.

        :param path: Path to dump config to.
        :param cfg: The in-memory config object to dump.
        :param opts: Other options required by a subclass.
        """

    def parse_include(self, ref_dict: Optional[dict] = None) -> None:
        """
        Recursively process include directives in a config object.

        Recursively traverse the dictionary, replacing include tags with the contents of the files
        they specify. Assumes a section/key/value structure. YAML provides this functionality in its
        own loader.

        :param ref_dict: A config object to process instead of the object's own data.
        """
        if ref_dict is None:
            ref_dict = self.data
        for key, value in copy.deepcopy(ref_dict).items():
            if isinstance(value, dict):
                self.parse_include(ref_dict[key])
            elif isinstance(value, str):
                if m := re.match(r"^\s*%s\s+(.*)" % _INCLUDE_TAG, value):
                    filepaths = yaml.safe_load(m[1])
                    self.update_values(self._load_paths(filepaths))
                    del ref_dict[key]

    def reify_scalar_str(self, s: str) -> Union[bool, float, int, str]:
        """
        Reify a string to a Python object, using YAML. Jinja2 templates will be passed as-is.

        :param s: The string to reify.
        """
        try:
            r = yaml.safe_load(s)
        except yaml.YAMLError:
            return s
        return r

    def update_values(self, src: Union[dict, Config], dst: Optional[Config] = None):
        """
        Updates a Config object.

        Update the instance's own data (or, optionally, that of the specifed Config object) with the
        values provided by another dictionary or Config object.

        :param src: The dictionary with new data to use.
        :param dst: The Config to update with the new data.
        """
        srcdict = src.data if isinstance(src, Config) else src
        dstcfg = self if dst is None else dst
        for key, new_val in srcdict.items():
            if isinstance(new_val, dict):
                if isinstance(dstcfg.get(key), dict):
                    self.update_values(new_val, dstcfg[key])
                else:
                    dstcfg[key] = new_val
            else:
                dstcfg[key] = new_val

    # Private methods

    def _depth(self, tree: dict) -> int:
        """
        The depth of this config's hierarchy.

        :param tree: A (sub)tree in the config.
        :return: The length of the longest path to a value in the config.
        """
        return (max(map(self._depth, tree.values())) + 1) if isinstance(tree, dict) else 0


class INIConfig(Config):
    """
    Concrete class to handle INI config files.
    """

    def __init__(
        self,
        config_file: str,
        space_around_delimiters: bool = True,
    ):
        """
        Construct an INIConfig object.

        Spaces may be included for INI format, but should be excluded for bash.

        :param config_file: Path to the config file to load.
        :param space_around_delimiters: Include spaces around delimiters?
        """
        super().__init__(config_file)
        self.space_around_delimiters = space_around_delimiters
        self.parse_include()

    # Private methods

    def _load(self, config_file: OptionalPath) -> dict:
        """
        Reads and parses an INI file.

        See docs for Config._load().

        :param config_file: Path to config file to load.
        """
        # The protected _sections method is the most straightforward way to get at the dict
        # representation of the parse config.

        cfg = configparser.ConfigParser()
        cfg.optionxform = str  # type: ignore
        sections = cfg._sections  # type: ignore # pylint: disable=protected-access
        with readable(config_file) as f:
            raw = f.read()
        try:
            cfg.read_string(raw)
            return dict(sections)
        except configparser.MissingSectionHeaderError:
            cfg.read_string("[top]\n" + raw)
            return dict(sections.get("top"))

    # Public methods

    def dump(self, path: OptionalPath) -> None:
        """
        Dumps the config in INI format.

        :param path: Path to dump config to.
        """
        INIConfig.dump_dict(path, self.data, ns(space=self.space_around_delimiters))

    @staticmethod
    def dump_dict(path: OptionalPath, cfg: dict, opts: Optional[ns] = None) -> None:
        """
        Dumps a provided config dictionary in INI format.

        :param path: Path to dump config to.
        :param cfg: The in-memory config object to dump.
        :param space_around_delimiters: Place spaces around delimiters?
        """
        parser = configparser.ConfigParser()
        with writable(path) as f:
            try:
                parser.read_dict(cfg)
                parser.write(f, space_around_delimiters=opts.space if opts else True)
            except AttributeError:
                for key, value in cfg.items():
                    print(f"{key}={value}", file=f)


class NMLConfig(Config):
    """
    Concrete class to handle Fortran namelist files.
    """

    def __init__(self, config_file) -> None:
        super().__init__(config_file)
        self.parse_include()

    # Private methods

    def _load(self, config_file: OptionalPath) -> dict:
        """
        Reads and parses a Fortran namelist file.

        See docs for Config._load().

        :param config_file: Path to config file to load.
        """

        # f90nml returns OrderedDict objects to maintain the order of namelists in the namelist
        # files that it reads. But in Python 3.6+ the standard dict maintains order as well. Since
        # OrderedDict can cause problems downstream when serializing to YAML, convert OrderedDict
        # objects to standard dicts here.

        def from_od(d):
            return {key: from_od(val) if isinstance(val, dict) else val for key, val in d.items()}

        with readable(config_file) as f:
            return from_od(f90nml.read(f).todict())

    # Public methods

    def dump(self, path: OptionalPath) -> None:
        """
        Dumps the config in Fortran namelist format.

        :param path: Path to dump config to.
        """
        NMLConfig.dump_dict(path, self.data)

    @staticmethod
    def dump_dict(path: OptionalPath, cfg: dict, opts: Optional[ns] = None) -> None:
        """
        Dumps a provided config dictionary in Fortran namelist format.

        :param path: Path to dump config to.
        :param cfg: The in-memory config object to dump.
        :param opts: Other options required by a subclass.
        """

        # f90nml honors namelist and variable order if it receives an OrderedDict as input, so
        # ensure that it receives one.

        def to_od(d):
            return OrderedDict(
                {key: to_od(val) if isinstance(val, dict) else val for key, val in d.items()}
            )

        with writable(path) as f:
            f90nml.Namelist(to_od(cfg)).write(f, sort=False)


class YAMLConfig(Config):
    """
    Concrete class to handle YAML config files.
    """

    def __repr__(self) -> str:
        """
        The string representation of a YAMLConfig object.
        """
        return yaml.dump(self.data)

    # Private methods

    def _load(self, config_file: OptionalPath) -> dict:
        """
        Reads and parses a YAML file.

        See docs for Config._load().

        :param config_file: Path to config file to load.
        """
        loader = self._yaml_loader
        with readable(config_file) as f:
            try:
                return yaml.load(f.read(), Loader=loader)
            except yaml.constructor.ConstructorError as e:
                if e.problem:
                    if "unhashable" in e.problem:
                        msg = _MSGS.unhashable
                    else:
                        constructor = e.problem.split()[-1]
                        msg = _MSGS.unregistered_constructor.format(
                            config_file=config_file, constructor=constructor
                        )
                else:
                    msg = str(e)
                raise _log_and_error(msg) from e

    def _yaml_include(self, loader: yaml.Loader, node: yaml.SequenceNode) -> dict:
        """
        Returns a dictionary with include tags processed.

        :param loader: The YAML loader.
        :param node: A YAML node.
        """
        filepaths = loader.construct_sequence(node)
        return self._load_paths(filepaths)

    @property
    def _yaml_loader(self) -> type[yaml.SafeLoader]:
        """
        Set up the loader with the appropriate constructors.
        """
        loader = yaml.SafeLoader
        loader.add_constructor(_INCLUDE_TAG, self._yaml_include)
        return loader

    # Public methods

    def dump(self, path: OptionalPath) -> None:
        """
        Dumps the config in YAML format.

        :param path: Path to dump config to.
        """
        YAMLConfig.dump_dict(path, self.data)

    @staticmethod
    def dump_dict(path: OptionalPath, cfg: dict, opts: Optional[ns] = None) -> None:
        """
        Dumps a provided config dictionary in YAML format.

        :param path: Path to dump config to.
        :param cfg: The in-memory config object to dump.
        :param opts: Other options required by a subclass.
        """
        with writable(path) as f:
            yaml.dump(cfg, f, sort_keys=False)


class FieldTableConfig(YAMLConfig):
    """
    This class exists to write out a field_table format given that its configuration has been set by
    an input YAML file.
    """

    # Public methods

    def dump(self, path: OptionalPath) -> None:
        """
        Dumps the config in Field Table format.

        :param path: Path to dump config to.
        """
        FieldTableConfig.dump_dict(path, self.data)

    @staticmethod
    def dump_dict(path: OptionalPath, cfg: dict, opts: Optional[ns] = None) -> None:
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

        :param path: Path to dump config to.
        :param cfg: The in-memory config object to dump.
        :param opts: Other options required by a subclass.
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


# Public functions


def compare_configs(
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
    :return: False if config files had differences, otherwise True.
    """

    cfg_a = format_to_config(config_a_format)(config_a_path)
    cfg_b = format_to_config(config_b_format)(config_b_path)
    log.info("- %s", config_a_path)
    log.info("+ %s", config_b_path)
    log.info("-" * MSGWIDTH)
    return cfg_a.compare_config(cfg_b.data)


def format_to_config(cli_name: str) -> Type[Config]:
    """
    Maps a CLI format name to its corresponding Config class.

    :param cli_name: The format name as known to the CLI.
    :return: The appropriate Config class.
    """
    classes: Dict[str, type[Config]] = {
        FORMAT.fieldtable: FieldTableConfig,
        FORMAT.ini: INIConfig,
        FORMAT.nml: NMLConfig,
        FORMAT.yaml: YAMLConfig,
    }
    try:
        return classes[cli_name]
    except KeyError as e:
        raise _log_and_error(
            "Format '%s' should be one of: %s" % (e.args[0], ", ".join(classes.keys()))
        ) from e


def print_config_section(config: dict, key_path: List[str]) -> None:
    """
    Descends into the config via the given keys, then prints the contents of the located subtree as
    key=value pairs, one per line.
    """
    keys = []
    current_path = "<unknown>"
    for section in key_path:
        keys.append(section)
        current_path = " -> ".join(keys)
        try:
            subconfig = config[section]
        except KeyError as e:
            raise _log_and_error(f"Bad config path: {current_path}") from e
        if not isinstance(subconfig, dict):
            raise _log_and_error(f"Value at {current_path} must be a dictionary")
        config = subconfig
    output_lines = []
    for key, value in config.items():
        if type(value) not in (bool, float, int, str):
            raise _log_and_error(f"Non-scalar value {value} found at {current_path}")
        output_lines.append(f"{key}={value}")
    print("\n".join(sorted(output_lines)))


def realize_config(
    input_file: OptionalPath,
    input_format: str,
    output_file: OptionalPath,
    output_format: str,
    values_file: OptionalPath,
    values_format: Optional[str],
    values_needed: bool = False,
    dry_run: bool = False,
) -> bool:
    """
    Realize an output config based on an input config and an optional values-providing config.

    :param input_file: Input config file (stdin used when None).
    :param input_format: Format of the input config.
    :param output_file: Output config file (stdout used when None).
    :param output_format: Format of the output config.
    :param values_file: File providing values to modify input.
    :param values_format: Format of the values config file.
    :param values_needed: Provide a report about complete, missing, and template values.
    :param dry_run: Log output instead of writing to output.
    :return: True if no exception is raised.
    :raises: UWConfigError if errors are encountered.
    """

    input_obj = format_to_config(input_format)(config_file=input_file)
    input_obj.dereference_all()
    input_obj = _realize_config_update(input_obj, values_file, values_format)
    _realize_config_check_depths(input_obj, output_format)
    if values_needed:
        return _realize_config_values_needed(input_obj)
    if dry_run:
        log.info(input_obj)
    else:
        format_to_config(output_format).dump_dict(path=output_file, cfg=input_obj.data)
    return True


# Private functions


def _log_and_error(msg: str) -> Exception:
    """
    Log an error message and raise an exception.

    :param msg: The error message to log and to associate with raised exception.
    """
    log.error(msg)
    return UWConfigError(msg)


def _realize_config_check_depths(input_obj: Config, output_format: str) -> None:
    """
    Check that the depth of the input config does not exceed the output format's max.

    :param input_obj: The input config.
    :param output_format: The output format:
    :raises: UWConfigError on excessive input-config depth.
    """
    if (output_format == FORMAT.ini and input_obj.depth > 2) or (
        output_format == FORMAT.nml and input_obj.depth != 2
    ):
        msg = "Cannot write depth-%s input to type-'%s' output" % (input_obj.depth, output_format)
        log.error(msg)
        raise UWConfigError(msg)


def _realize_config_update(
    input_obj: Config, values_file: OptionalPath, values_format: Optional[str]
) -> Config:
    """
    Update config with values from another config, if given.

    :param input_obj: The config to update.
    :param values_file: File providing values to modify input.
    :param values_format: Format of the values config file.
    :return: The input config, possibly updated.
    """
    if values_file:
        log.debug("Before update, config has depth %s", input_obj.depth)
        values_format = values_format or get_file_type(values_file)
        values_obj = format_to_config(values_format)(config_file=values_file)
        log.debug("Values config has depth %s", values_obj.depth)
        input_obj.update_values(values_obj)
        input_obj.dereference_all()
        log.debug("After update, input config has depth %s", input_obj.depth)
    else:
        log.debug("Input config has depth %s", input_obj.depth)
    return input_obj


def _realize_config_values_needed(input_obj: Config) -> bool:
    """
    Print a report characterizing input values as complete, empty, or template placeholders.

    :param input_obj: The config to update.
    """
    complete, empty, template = input_obj.characterize_values(input_obj.data, parent="")
    log.info("Keys that are complete:")
    for var in complete:
        log.info(var)
    log.info("")
    log.info("Keys that have unfilled Jinja2 templates:")
    for var in template:
        log.info(var)
    log.info("")
    log.info("Keys that are set to empty:")
    for var in empty:
        log.info(var)
    return True


def _add_filters(env: jinja2.Environment) -> jinja2.Environment:
    def path_join(path_components: List[str]) -> str:
        if any(isinstance(x, jinja2.Undefined) for x in path_components):
            raise jinja2.exceptions.UndefinedError()
        return os.path.join(*path_components)

    filters = dict(
        path_join=path_join,
    )
    env.filters.update(filters)
    return env


def _dereference(val: _YAMLVal, context: dict) -> _YAMLVal:
    if isinstance(val, dict):
        return {k: _dereference(v, context) for k, v in val.items()}
    if isinstance(val, list):
        return [_dereference(v, context) for v in val]
    if isinstance(val, str):
        try:
            return _reify_scalar_str(
                yaml.safe_load(
                    _add_filters(jinja2.Environment(undefined=jinja2.DebugUndefined))
                    .from_string(f"'{val}'")
                    .render(**context)
                )
            )
        except Exception:
            pass
    return val


def _reify_scalar_str(s: str) -> Union[bool, float, int, str]:
    """
    Reify a string to a Python object, using YAML. Jinja2 templates will be passed as-is.

    :param s: The string to reify.
    """
    try:
        r = yaml.safe_load(s)
    except yaml.YAMLError:
        return s
    return r


# def _old_dereference(self, d: Optional[dict] = None, vals_dict: Optional[dict] = None) -> None:
#     """
#     Recursively render Jinja2 values in dictionary.

#     In general, this method should be called without arguments. Recursive calls made by the
#     method to itself will supply appropriate arguments.

#     :param d: Dictionary potentially containing Jinja2-template values.
#     :param vals_dict: Values to be used for rendering Jinja2 templates.
#     """
#     d = self.data if d is None else d
#     vals_dict = d if vals_dict is None else vals_dict
#     for key, val in d.items():
#         if isinstance(val, dict):
#             self._dereference(val, vals_dict)
#             continue
#         v_str = str(val)
#         if any((ele for ele in ["{{", "{%"] if ele in v_str)):
#             error_catcher = {}
#             # Find expressions first, and process them as a single template if they exist.
#             # Find individual double curly brace template in the string otherwise. We need
#             # one substitution template at a time so that we can opt to leave some un-filled
#             # when they are not yet set. For example, we can save cycle-dependent templates
#             # to fill in at run time.
#             if "{%" in val:
#                 # Treat entire line as a single template.
#                 templates = [v_str]
#             else:
#                 # Separate out all the double curly bracket pairs.
#                 templates = re.findall(r"{{[^}]*}}|\S", v_str)
#             data = []
#             for template in templates:
#                 # Creating the config object for the template like this, gives us access to
#                 # all the keys in the current section without the need to reference the
#                 # current section name, and to the other sections with dot values. Also make
#                 # environment variables available with env prefix.
#                 if d == vals_dict:
#                     values = {**os.environ, **vals_dict}
#                 else:
#                     values = {**os.environ, **d, **vals_dict}
#                 try:
#                     j2tmpl = J2Template(
#                         values=values,
#                         template_str=template,
#                         loader_args={"undefined": jinja2.StrictUndefined},
#                     )
#                 except jinja2.exceptions.TemplateAssertionError as e:
#                     msg = _MSGS.unregistered_filter.format(
#                         filter=repr(e).split()[-1][:-3], key=key
#                     )
#                     raise _log_and_error(msg) from e
#                 rendered = template
#                 try:
#                     # Fill in a template that has the appropriate variables set.
#                     rendered = j2tmpl.render()
#                 except jinja2.exceptions.UndefinedError:
#                     # Leave a templated field as-is in the resulting dict.
#                     error_catcher[template] = "UndefinedError"
#                 except TypeError:
#                     error_catcher[template] = "TypeError"
#                 except ZeroDivisionError:
#                     error_catcher[template] = "ZeroDivisionError"
#                 except Exception as e:
#                     # Fail on any other exception...something is probably wrong.
#                     msg = f"{key}: {template}"
#                     log.exception(msg)
#                     raise e
#                 data.append(rendered)
#                 for tmpl, err in error_catcher.items():
#                     log.debug("%s raised %s", tmpl, err)
#             for tmpl, rendered in zip(templates, data):
#                 v_str = v_str.replace(tmpl, rendered)
#             # Put the full template line back together as it was, filled or not, and make a
#             # guess on its intended type.
#             d[key] = self.reify_scalar_str(v_str)
