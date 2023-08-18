"""
The abstract Config class and its format-specific subclasses.
"""
from __future__ import annotations

import configparser
import copy
import inspect
import json
import logging
import os
import re
import sys
from abc import ABC, abstractmethod
from collections import OrderedDict, UserDict
from types import SimpleNamespace as ns
from typing import List, Optional, Union

import f90nml
import jinja2
import yaml

from uwtools import exceptions, logger
from uwtools.exceptions import UWConfigError
from uwtools.j2template import J2Template
from uwtools.logger import Logger
from uwtools.utils import cli_helpers

msgs = ns(
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

    def __init__(self, config_path: str, log_name: Optional[str] = None) -> None:
        """
        Construct a Config object.

        :param config_path: Path to the config file to load.
        :param log_name: Name of logger object to log to.
        """
        super().__init__()
        self.config_path = config_path
        self.log = logging.getLogger(log_name)
        self.update(self._load(self.config_path))

    def __repr__(self) -> str:
        """
        The string representation of a Config object.
        """
        return json.dumps(self.data)

    # Private methods

    @abstractmethod
    def _load(self, config_path: str) -> dict:
        """
        Reads and parses a config file.

        Returns the result of loading and parsing the specified config file.

        :param config_path: Path to config file to load.
        """

    def _load_paths(self, filepaths: List[str]) -> dict:
        """
        Merge and return the contents of a collection of config files.

        :param filepaths: Paths to the config files to read and merge.
        """
        cfg = {}
        for filepath in filepaths:
            if not os.path.isabs(filepath):
                filepath = os.path.join(os.path.dirname(self.config_path), filepath)
            cfg.update(self._load(config_path=filepath))
        return cfg

    # Public methods

    def compare_config(self, dict1: dict, dict2: Optional[dict] = None) -> None:
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
                self.log.info(msg)

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
                            msg = msgs.unregistered_filter.format(
                                filter=repr(e).split()[-1][:-3], key=key
                            )
                            self.log.exception(msg)
                            raise exceptions.UWConfigError(msg)
                        rendered = template
                        try:
                            # Fill in a template that has the appropriate variables set.
                            rendered = j2tmpl.render_template()
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
                            self.log.exception(msg)
                            raise e

                        data.append(rendered)
                        for tmpl, err in error_catcher.items():
                            msg = f"{func_name}: {tmpl} raised {err}"
                            self.log.debug(msg)

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

    def dictionary_depth(self, config_dict: dict) -> int:
        """
        The depth of a dictionary.

        :param config_dict: The dictionary whose depth to find.
        """
        if isinstance(config_dict, dict):
            return 1 + (max(map(self.dictionary_depth, config_dict.values())))
        return 0

    def iterate_values(
        self,
        config_dict: dict,
        set_var: List[str],
        jinja2_var: List[str],
        empty_var: List[str],
        parent: str,
    ) -> None:
        """
        Characterize values as complete, empty, or Jinja2 templates.

        complete -> set_var, empty -> empty_var, templates -> jinja2_var

        :param config_dict: The dictionary to examine.
        :param set_var: Complete values.
        :param jinja2_var: Jinja2 template values.
        :param empty_var: Empty values.
        :param parent: Parent key.
        """
        for key, val in config_dict.items():
            if isinstance(val, dict):
                set_var.append(f"    {parent}{key}")
                new_parent = f"{parent}{key}."
                self.iterate_values(val, set_var, jinja2_var, empty_var, new_parent)
            elif isinstance(val, list):
                set_var.append(f"    {parent}{key}")
                for item in val:
                    if isinstance(item, dict):
                        self.iterate_values(item, set_var, jinja2_var, empty_var, parent)
            elif "{{" in str(val) or "{%" in str(val):
                jinja2_var.append(f"    {parent}{key}: {val}")
            elif val == "" or val is None:
                empty_var.append(f"    {parent}{key}")
            else:
                set_var.append(f"    {parent}{key}")

    @abstractmethod
    def dump_file(self, path: str) -> None:
        """
        Dumps the config as a file.

        :param path: Path to dump config to.
        """

    @staticmethod
    @abstractmethod
    def dump_file_from_dict(path: str, cfg: dict, opts: Optional[ns] = None) -> None:
        """
        Dumps a provided config dictionary as a file.

        :param path: Path to dump config to.
        :param cfg: The in-memory config object to dump.
        :param opts: Other options required by a subclass.
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

    @logger.verbose()
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


class F90Config(Config):
    """
    Concrete class to handle Fortran namelist files.
    """

    def __init__(self, config_path: str, log_name: Optional[str] = None) -> None:
        super().__init__(config_path, log_name)
        self.parse_include()

    # Private methods

    def _load(self, config_path: str) -> dict:
        """
        Reads and parses a Fortran namelist file.

        See docs for Config._load().

        :param config_path: Path to config file to load.
        """
        with open(config_path, "r", encoding="utf-8") as f:
            cfg = f90nml.read(f).todict(complex_tuple=False)
        return self.from_ordereddict(cfg)

    # Public methods

    def dump_file(self, path: str) -> None:
        """
        Dumps the config as a Fortran namelist file.

        :param path: Path to dump config to.
        """
        F90Config.dump_file_from_dict(path, self.data)

    @staticmethod
    def dump_file_from_dict(path: str, cfg: dict, opts: Optional[ns] = None) -> None:
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
        with open(path, "w", encoding="utf-8") as file_name:
            f90nml.Namelist(nml).write(file_name, sort=False)


class INIConfig(Config):
    """
    Concrete class to handle INI config files.
    """

    def __init__(
        self,
        config_path: str,
        log_name: Optional[str] = None,
        space_around_delimiters: bool = True,
    ):
        """
        Construct an INIConfig object.

        Spaces may be included for INI format, but should be excluded for bash.

        :param config_path: Path to the config file to load.
        :param log_name: Name of logger object to log to.
        :param space_around_delimiters: Include spaces around delimiters?
        """
        super().__init__(config_path, log_name)
        self.space_around_delimiters = space_around_delimiters
        self.parse_include()

    # Private methods

    def _load(self, config_path: str) -> dict:
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
        try:
            cfg.read(config_path)
        except configparser.MissingSectionHeaderError:
            with open(config_path, "r", encoding="utf-8") as file_name:
                cfg.read_string("[top]\n" + file_name.read())
                ret_cfg = dict(sections.get("top"))
                ret_cfg = self.from_ordereddict(ret_cfg)
                return ret_cfg
        return self.from_ordereddict(dict(sections))

    # Public methods

    def dump_file(self, path: str) -> None:
        """
        Dumps the config as an INI file.

        :param path: Path to dump config to.
        """
        INIConfig.dump_file_from_dict(path, self.data, ns(space=self.space_around_delimiters))

    @staticmethod
    def dump_file_from_dict(path: str, cfg: dict, opts: Optional[ns] = None) -> None:
        """
        Dumps a provided config dictionary as an INI file.

        :param path: Path to dump config to.
        :param cfg: The in-memory config object to dump.
        :param space_around_delimiters: Place spaces around delimiters?
        """
        parser = configparser.ConfigParser()
        with open(path, "w", encoding="utf-8") as file_name:
            try:
                parser.read_dict(cfg)
                parser.write(file_name, space_around_delimiters=opts.space if opts else True)
            except AttributeError:
                for key, value in cfg.items():
                    file_name.write(f"{key}={value}\n")


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

    def _load(self, config_path: str) -> dict:
        """
        Reads and parses a YAML file.

        See docs for Config._load().

        :param config_path: Path to config file to load.
        """
        loader = self._yaml_loader
        with open(config_path, "r", encoding="utf-8") as file_name:
            try:
                cfg = yaml.load(file_name, Loader=loader)
            except yaml.constructor.ConstructorError as e:
                if e.problem:
                    if "unhashable" in e.problem:
                        msg = msgs.unhashable
                    else:
                        constructor = e.problem.split()[-1]
                        msg = msgs.unregistered_constructor.format(
                            config_path=config_path, constructor=constructor
                        )
                else:
                    msg = str(e)
                self.log.exception(msg)
                raise exceptions.UWConfigError(msg)
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

    def dump_file(self, path: str) -> None:
        """
        Dumps the config as a YAML file.

        :param path: Path to dump config to.
        """
        YAMLConfig.dump_file_from_dict(path, self.data)

    @staticmethod
    def dump_file_from_dict(path: str, cfg: dict, opts: Optional[ns] = None) -> None:
        """
        Dumps a provided config dictionary as a YAML file.

        :param path: Path to dump config to.
        :param cfg: The in-memory config object to dump.
        :param opts: Other options required by a subclass.
        """
        with open(path, "w", encoding="utf-8") as file_name:
            yaml.dump(cfg, file_name, sort_keys=False)


class FieldTableConfig(YAMLConfig):
    """
    This class exists to write out a field_table format given that its configuration has been set by
    an input YAML file.
    """

    # Public methods

    def dump_file(self, path: str) -> None:
        """
        Dumps the config as a Field Table file.

        :param path: Path to dump config to.
        """
        FieldTableConfig.dump_file_from_dict(path, self.data)

    @staticmethod
    def dump_file_from_dict(path: str, cfg: dict, opts: Optional[ns] = None) -> None:
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
        with open(path, "w", encoding="utf-8") as file_name:
            file_name.write("\n".join(lines))


# Private functions


def _log_and_error(msg: str, log: Logger) -> None:
    """
    Will log a user-provided error message and raise a UWConfigError with the same message.
    """
    log.error(msg)
    raise UWConfigError(msg)


# Public functions


def create_config_obj(
    input_base_file: str,
    compare: bool = False,
    config_file: Optional[str] = None,
    config_file_type: Optional[str] = None,
    dry_run: bool = False,
    input_file_type: Optional[str] = None,
    log: Optional[Logger] = None,
    log_file: Optional[str] = None,
    outfile: Optional[str] = None,
    output_file_type: Optional[str] = None,
    quiet: bool = False,
    show_format: bool = False,
    values_needed: bool = False,
    verbose: bool = False,
):
    """
    Main section for processing config file.
    """
    if log is None:
        name = f"{inspect.stack()[0][3]}"
        log = cli_helpers.setup_logging(
            log_file=log_file or "/dev/stdout",
            log_name=name,
            quiet=quiet,
            verbose=verbose,
        )

    infile_type = input_file_type or cli_helpers.get_file_type(input_base_file)

    config_class = globals()[f"{infile_type}Config"]
    config_obj = config_class(input_base_file, log_name=log.name)

    if config_file:
        config_file_type = config_file_type or cli_helpers.get_file_type(config_file)

        user_config_obj = globals()[f"{config_file_type}Config"](config_file)

        if config_file_type != infile_type:
            config_depth = user_config_obj.dictionary_depth(user_config_obj.data)
            input_depth = config_obj.dictionary_depth(config_obj.data)

            if input_depth < config_depth:
                log.critical(f"{config_file} not compatible with input file")
                raise ValueError("Set config failure: config object not compatible with input file")

        if compare:
            log.info(f"- {input_base_file}")
            log.info(f"+ {config_file}")
            log.info("-" * 80)
            config_obj.compare_config(user_config_obj)
            return

        config_obj.update_values(user_config_obj)

    config_obj.dereference_all()

    if values_needed:
        set_var: List[str] = []
        jinja2_var: List[str] = []
        empty_var: List[str] = []
        config_obj.iterate_values(config_obj.data, set_var, jinja2_var, empty_var, parent="")
        log.info("Keys that are complete:")
        for var in set_var:
            log.info(var)
        log.info("")
        log.info("Keys that have unfilled jinja2 templates:")
        for var in jinja2_var:
            log.info(var)
        log.info("")
        log.info("Keys that are set to empty:")
        for var in empty_var:
            log.info(var)
        return

    if dry_run:
        # Apply switch to allow user to view the results of config instead of writing to disk.
        log.info(config_obj)
        return

    if outfile:
        outfile_type = output_file_type or cli_helpers.get_file_type(outfile)
        if outfile_type == infile_type:
            config_obj.dump_file(outfile)
        else:
            dump_method = globals()[f"{outfile_type}Config"].dump_file_from_dict
            if show_format:
                help(dump_method)
            else:
                # Check for incompatible conversion objects:
                input_depth = config_obj.dictionary_depth(config_obj.data)
                if (outfile_type == "INI" and input_depth > 2) or (
                    outfile_type == "F90" and input_depth != 2
                ):
                    err_msg = "Set config failure: incompatible file types"
                    log.critical(err_msg)
                    raise ValueError(err_msg)
                # Dump to file:
                dump_method(path=outfile, cfg=config_obj)


def print_config_section(config: dict, key_path: List[str], log: Logger) -> None:
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
        except KeyError:
            _log_and_error(f"Bad config path: {current_path}", log)
        if not isinstance(subconfig, dict):
            _log_and_error(f"Value at {current_path} must be a dictionary", log)
        config = subconfig
    output_lines = []
    for key, value in config.items():
        if type(value) not in (bool, float, int, str):
            _log_and_error(f"Non-scalar value {value} found at {current_path}", log)
        output_lines.append(f"{key}={value}")
    print("\n".join(sorted(output_lines)))
