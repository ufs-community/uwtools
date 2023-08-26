"""
The abstract Config class and its format-specific subclasses.
"""

from __future__ import annotations

import configparser
import copy
import json
import logging
import os
import re
import sys
from abc import ABC, abstractmethod
from collections import OrderedDict, UserDict
from types import SimpleNamespace as ns
from typing import Dict, List, Optional, Tuple, Type, Union

import f90nml
import jinja2
import yaml

from uwtools.config.j2template import J2Template
from uwtools.exceptions import UWConfigError
from uwtools.types import DefinitePath, OptionalPath
from uwtools.utils.file import get_file_type, readable, writable

MSGS = ns(
    unhashable="""
ERROR:
The input config file may contain a Jinja2 templated value at the location listed above. Ensure the
value is enclosed in quotes.
""".strip(),
    unregistered_constructor="""
ERROR:
The input config file contains a constructor that is not registered with the uwtools package.

constructor: {constructor}
config file: {config_path}

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


class Config(ABC, UserDict):
    """
    A base class specifying (and partially implementing) methods to read, manipulate, and write
    several configuration-file formats.
    """

    def __init__(self, config_path: OptionalPath = None) -> None:
        """
        Construct a Config object.

        :param config_path: Path to the config file to load.
        """
        super().__init__()
        self._config_path = str(config_path) if config_path else None
        self.update(self._load(self._config_path))
        self.depth = self._depth(self.data)

    def __repr__(self) -> str:
        """
        The string representation of a Config object.
        """
        return json.dumps(self.data)

    # Private methods

    @abstractmethod
    def _load(self, config_path: OptionalPath) -> dict:
        """
        Reads and parses a config file.

        Returns the result of loading and parsing the specified config file, or stdin if no file is
        given.

        :param config_path: Path to config file to load.
        """

    def _load_paths(self, config_paths: List[str]) -> dict:
        """
        Merge and return the contents of a collection of config files.

        :param config_paths: Paths to the config files to read and merge.
        """
        cfg = {}
        for config_path in config_paths:
            if not os.path.isabs(config_path):
                if self._config_path:
                    config_path = os.path.join(os.path.dirname(self._config_path), config_path)
                else:
                    raise _log_and_error(
                        "Reading from stdin, a relative path was encountered: %s" % config_path
                    )
            cfg.update(self._load(config_path=config_path))
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
                complete.append(f"    {parent}{key}")
                for item in val:
                    if isinstance(item, dict):
                        c, e, t = self.characterize_values(item, parent)
                        complete, empty, template = complete + c, empty + e, template + t
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
                logging.info(msg)

        return not diffs

    def dereference(
        self, ref_dict: Optional[dict] = None, full_dict: Optional[dict] = None
    ) -> None:
        """
        Recursively replace Jinja2 templates in a Config object.

        In general, this method should be called without arguments. Recursive calls made by the
        method to itself will supply appropriate arguments.

        :param ref_dict: Dictionary potentially containing to-be-rendered Jinja2 templates.
        :param full_dict: Dictionary providing values to be used for rendering Jinja2 templates.
        """
        ref_dict = self.data if ref_dict is None else ref_dict
        full_dict = self.data if full_dict is None else full_dict

        # Choosing sys._getframe() here because it's more efficient than other inspect methods.

        func_name = f"{self.__class__.__name__}.{sys._getframe().f_code.co_name}"  # pylint: disable=protected-access

        for key, val in ref_dict.items():
            if isinstance(val, dict):
                self.dereference(val, full_dict)
            else:
                # Save a bit of compute and only do this part for strings that contain the jinja
                # double brackets.
                v_str = str(val)
                is_a_template = any((ele for ele in ["{{", "{%"] if ele in v_str))
                if is_a_template:
                    error_catcher = {}
                    # Find expressions first, and process them as a single template if they exist.
                    # Find individual double curly brace template in the string otherwise. We need
                    # one substitution template at a time so that we can opt to leave some un-filled
                    # when they are not yet set. For example, we can save cycle-dependent templates
                    # to fill in at run time.
                    if "{%" in val:
                        # Treat entire line as a single template.
                        templates = [v_str]
                    else:
                        # Separate out all the double curly bracket pairs.
                        templates = re.findall(r"{{[^}]*}}|\S", v_str)
                    data = []
                    for template in templates:
                        # Creating the config object for the template like this, gives us access to
                        # all the keys in the current section without the need to reference the
                        # current section name, and to the other sections with dot values. Also make
                        # environment variables available with env prefix.
                        if ref_dict == full_dict:
                            config_obj = {**os.environ, **full_dict}
                        else:
                            config_obj = {**os.environ, **ref_dict, **full_dict}
                        try:
                            j2tmpl = J2Template(
                                configure_obj=config_obj,
                                template_str=template,
                                loader_args={"undefined": jinja2.StrictUndefined},
                            )
                        except jinja2.exceptions.TemplateAssertionError as e:
                            msg = MSGS.unregistered_filter.format(
                                filter=repr(e).split()[-1][:-3], key=key
                            )
                            raise _log_and_error(msg) from e
                        rendered = template
                        try:
                            # Fill in a template that has the appropriate variables set.
                            rendered = j2tmpl.render()
                        except jinja2.exceptions.UndefinedError:
                            # Leave a templated field as-is in the resulting dict.
                            error_catcher[template] = "UndefinedError"
                        except TypeError:
                            error_catcher[template] = "TypeError"
                        except ZeroDivisionError:
                            error_catcher[template] = "ZeroDivisionError"
                        except Exception as e:
                            # Fail on any other exception...something is probably wrong.
                            msg = f"{key}: {template}"
                            logging.exception(msg)
                            raise e

                        data.append(rendered)
                        for tmpl, err in error_catcher.items():
                            msg = f"{func_name}: {tmpl} raised {err}"
                            logging.debug(msg)

                    # Put the full template line back together as it was, filled or not, and make a
                    # guess on its intended type.
                    ref_dict[key] = self.str_to_type("".join(data))

    def dereference_all(self) -> None:
        """
        Dereference iteratively until no Jinja2 templates remain.
        """
        prev = copy.deepcopy(self.data)
        self.dereference()
        while prev != self.data:
            self.dereference()
            prev = copy.deepcopy(self.data)

    @staticmethod
    @abstractmethod
    def dump_dict(path: OptionalPath, cfg: dict, opts: Optional[ns] = None) -> None:
        """
        Dumps a provided config dictionary as a file.

        :param path: Path to dump config to.
        :param cfg: The in-memory config object to dump.
        :param opts: Other options required by a subclass.
        """

    @abstractmethod
    def dump_file(self, path: DefinitePath) -> None:
        """
        Dumps the config as a file.

        :param path: Path to dump config to.
        """

    def from_ordereddict(self, in_dict: dict) -> dict:
        """
        Recursively replaces all OrderedDict objects with basic dict objects.

        :param: in_dict: A dictionary potentially containing OrderedDict objects
        """
        if isinstance(in_dict, OrderedDict):
            in_dict = dict(in_dict)
        for sect, keys in in_dict.items():
            if isinstance(keys, OrderedDict):
                in_dict[sect] = dict(keys)
        return in_dict

    def parse_include(self, ref_dict: Optional[dict] = None):
        """
        Recursively process !INCLUDE directives in a config object.

        Recursively traverses the dictionary, replacing !INCLUDE tags with the contents of the files
        they specify. Assumes a section/key/value structure. YAML provides this functionality in its
        own loader.

        :param ref_dict: A config object to process instead of the object's own data.
        """
        if ref_dict is None:
            ref_dict = self.data
        for key, value in copy.deepcopy(ref_dict).items():
            if isinstance(value, dict):
                self.parse_include(ref_dict[key])
            elif isinstance(value, str) and "!INCLUDE" in value:
                filepaths = value.lstrip("!INCLUDE [").rstrip("]").split(",")
                # Update the dictionary with the values in the included file.
                self.update_values(self._load_paths(filepaths))
                del ref_dict[key]

    def str_to_type(self, s: str) -> Union[bool, float, int, str]:
        """
        Reify a string to a Python object, if possible.

        Try to convert Boolean-ish values to bool objects, int-ish values to ints objects, and
        float-ish values to float objects. Return the original string if none of these apply.

        :param s: The string to reify.
        """
        s = s.strip("\"'")
        if s.lower() in ["true", "yes", "yeah"]:
            return True
        if s.lower() in ["false", "no", "nope"]:
            return False
        # int
        try:
            return int(s)
        except ValueError:
            pass
        # float
        try:
            return float(s)
        except ValueError:
            pass
        return s

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
        config_path: str,
        space_around_delimiters: bool = True,
    ):
        """
        Construct an INIConfig object.

        Spaces may be included for INI format, but should be excluded for bash.

        :param config_path: Path to the config file to load.
        :param space_around_delimiters: Include spaces around delimiters?
        """
        super().__init__(config_path)
        self.space_around_delimiters = space_around_delimiters
        self.parse_include()

    # Private methods

    def _load(self, config_path: OptionalPath) -> dict:
        """
        Reads and parses an INI file.

        See docs for Config._load().

        :param config_path: Path to config file to load.
        """
        # The protected _sections method is the most straightforward way to get at the dict
        # representation of the parse config.

        cfg = configparser.ConfigParser(dict_type=OrderedDict)
        cfg.optionxform = str  # type: ignore
        sections = cfg._sections  # type: ignore # pylint: disable=protected-access
        with readable(config_path) as f:
            raw = f.read()
        try:
            cfg.read_string(raw)
            d = dict(sections)
        except configparser.MissingSectionHeaderError:
            cfg.read_string("[top]\n" + raw)
            d = dict(sections.get("top"))
        return self.from_ordereddict(d)

    # Public methods

    @staticmethod
    def dump_dict(path: OptionalPath, cfg: dict, opts: Optional[ns] = None) -> None:
        """
        Dumps a provided config dictionary as an INI file.

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

    def dump_file(self, path: DefinitePath) -> None:
        """
        Dumps the config as an INI file.

        :param path: Path to dump config to.
        """
        INIConfig.dump_dict(path, self.data, ns(space=self.space_around_delimiters))


class NMLConfig(Config):
    """
    Concrete class to handle Fortran namelist files.
    """

    def __init__(self, config_path) -> None:
        super().__init__(config_path)
        self.parse_include()

    # Private methods

    def _load(self, config_path: OptionalPath) -> dict:
        """
        Reads and parses a Fortran namelist file.

        See docs for Config._load().

        :param config_path: Path to config file to load.
        """
        with readable(config_path) as f:
            cfg = f90nml.read(f).todict(complex_tuple=False)
        return self.from_ordereddict(cfg)

    # Public methods

    @staticmethod
    def dump_dict(path: OptionalPath, cfg: dict, opts: Optional[ns] = None) -> None:
        """
        Dumps a provided config dictionary as a Fortran namelist file.

        :param path: Path to dump config to.
        :param cfg: The in-memory config object to dump.
        :param opts: Other options required by a subclass.
        """
        nml = OrderedDict(cfg)
        for sect, keys in nml.items():
            if isinstance(keys, dict):
                nml[sect] = OrderedDict(keys)
        with writable(path) as f:
            f90nml.Namelist(nml).write(f, sort=False)

    def dump_file(self, path: DefinitePath) -> None:
        """
        Dumps the config as a Fortran namelist file.

        :param path: Path to dump config to.
        """
        NMLConfig.dump_dict(path, self.data)


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

    def _load(self, config_path: OptionalPath) -> dict:
        """
        Reads and parses a YAML file.

        See docs for Config._load().

        :param config_path: Path to config file to load.
        """
        loader = self._yaml_loader
        with readable(config_path) as f:
            try:
                cfg = yaml.load(f, Loader=loader)
            except yaml.constructor.ConstructorError as e:
                if e.problem:
                    if "unhashable" in e.problem:
                        msg = MSGS.unhashable
                    else:
                        constructor = e.problem.split()[-1]
                        msg = MSGS.unregistered_constructor.format(
                            config_path=config_path, constructor=constructor
                        )
                else:
                    msg = str(e)
                raise _log_and_error(msg) from e
        return self.from_ordereddict(cfg)

    def _yaml_include(self, loader: yaml.Loader, node: yaml.SequenceNode) -> dict:
        """
        Returns a dictionary with YAML !INCLUDE tags processed.

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
        loader.add_constructor("!INCLUDE", self._yaml_include)
        return loader

    # Public methods

    @staticmethod
    def dump_dict(path: OptionalPath, cfg: dict, opts: Optional[ns] = None) -> None:
        """
        Dumps a provided config dictionary as a YAML file.

        :param path: Path to dump config to.
        :param cfg: The in-memory config object to dump.
        :param opts: Other options required by a subclass.
        """
        with writable(path) as f:
            yaml.dump(cfg, f, sort_keys=False)

    def dump_file(self, path: DefinitePath) -> None:
        """
        Dumps the config as a YAML file.

        :param path: Path to dump config to.
        """
        YAMLConfig.dump_dict(path, self.data)


class FieldTableConfig(YAMLConfig):
    """
    This class exists to write out a field_table format given that its configuration has been set by
    an input YAML file.
    """

    # Public methods

    @staticmethod
    def dump_dict(path: OptionalPath, cfg: dict, opts: Optional[ns] = None) -> None:
        """
        Dumps a provided config dictionary as a Field Table file.

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

    def dump_file(self, path: DefinitePath) -> None:
        """
        Dumps the config as a Field Table file.

        :param path: Path to dump config to.
        """
        FieldTableConfig.dump_dict(path, self.data)


# Private functions


def _cli_name_to_config(cli_name: str) -> Type[Config]:
    """
    Maps a CLI format name to its corresponding Config class.

    :param cli_name: The format name as known to the CLI.
    :return: The appropriate Config class.
    """
    classes: Dict[str, type[Config]] = {
        "fieldtable": FieldTableConfig,
        "ini": INIConfig,
        "nml": NMLConfig,
        "yaml": YAMLConfig,
    }
    try:
        return classes[cli_name]
    except KeyError as e:
        raise _log_and_error(
            "Format '%s' should be one of: %s" % (e.args[0], ", ".join(classes.keys()))
        ) from e


def _log_and_error(msg: str) -> Exception:
    """
    Log an error message and raise an exception.

    :param msg: The error message to log and to associate with raised exception.
    """
    logging.error(msg)
    return UWConfigError(msg)


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

    cfg_a = _cli_name_to_config(config_a_format)(config_a_path)
    cfg_b = _cli_name_to_config(config_b_format)(config_b_path)
    logging.info("- %s", config_a_path)
    logging.info("+ %s", config_b_path)
    logging.info("-" * 69)
    return cfg_a.compare_config(cfg_b.data)


def print_config_section(config: dict, key_path: List[str]) -> None:
    """
    Descends into the config via the given keys, then prints the contents of the located subtree as
    key=value pairs, one per line.
    """
    keys = []
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
        logging.debug("Before update, config has depth %s", input_obj.depth)
        values_format = values_format or get_file_type(values_file)
        values_obj = _cli_name_to_config(values_format)(config_path=values_file)
        logging.debug("Values config has depth %s", values_obj.depth)
        input_obj.update_values(values_obj)
        input_obj.dereference_all()
        logging.debug("After update, input config has depth %s", input_obj.depth)
    else:
        logging.debug("Input config has depth %s", input_obj.depth)
    return input_obj


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

    input_obj = _cli_name_to_config(input_format)(config_path=input_file)
    input_obj.dereference_all()

    input_obj = _realize_config_update(input_obj, values_file, values_format)
    # if values_file:
    #     logging.debug("Before update, config has depth %s", input_obj.depth)
    #     values_format = values_format or get_file_type(values_file)
    #     values_obj = _cli_name_to_config(values_format)(config_path=values_file)
    #     logging.debug("Values config has depth %s", values_obj.depth)
    #     input_obj.update_values(values_obj)
    #     input_obj.dereference_all()
    #     logging.debug("After update, input config has depth %s", input_obj.depth)
    # else:
    #     logging.debug("Input config has depth %s", input_obj.depth)

    if (output_format == "ini" and input_obj.depth > 2) or (
        output_format == "nml" and input_obj.depth != 2
    ):
        msg = "Cannot write depth-%s input to type-'%s' output" % (input_obj.depth, output_format)
        logging.error(msg)
        raise UWConfigError(msg)

    if values_needed:
        complete, empty, template = input_obj.characterize_values(input_obj.data, parent="")
        logging.info("Keys that are complete:")
        for var in complete:
            logging.info(var)
        logging.info("")
        logging.info("Keys that have unfilled Jinja2 templates:")
        for var in template:
            logging.info(var)
        logging.info("")
        logging.info("Keys that are set to empty:")
        for var in empty:
            logging.info(var)
        return True

    if dry_run:
        logging.info(input_obj)
    else:
        _cli_name_to_config(output_format).dump_dict(path=output_file, cfg=input_obj.data)

    return True
