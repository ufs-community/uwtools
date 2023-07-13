"""
This file contains the Config file and its subclasses for a variety of dicatable file types.
"""
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
from uwtools.j2template import J2Template
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
    This base class provides the interface to methods used to read in several configuration file
    types and manipulate them as such.

    Attributes
    ----------

    config_path
        The file path to the configuration file to be parsed.

    Methods
    -------

    _load()
        Abstract method used as an interface to load a config file

    dump_file(output_path)
        Abstract method used as an interface to write a file to disk

    from_ordereddict(in_dict)
        Given a dictionary, replaces instances of OrderedDict with a regular dictionary

    parse_include()
        Traverses the dictionary treating the !INCLUDE path the same as
        is done by pyyaml.

    replace_templates()
        Traverses the dictionary and renders any Jinja2 templated
        fields.

    update_values()
        Update the values in an existing dictionary with values providedv by a second dictionary.
        Keep any of the values that are not present in the second dictionary.
    """

    def __init__(self, config_path: Optional[str] = None, log_name: Optional[str] = None) -> None:
        """
        Parameters
        ----------
        config_path
            See class-level docstring
        log_name
            Name to be used in log messages
        """
        super().__init__()
        self.config_path = config_path
        self.log = logging.getLogger(log_name)

    def __repr__(self):
        """
        This method will return configure contents.
        """
        return json.dumps(self.data)

    # Private methods

    @abstractmethod
    def _load(self, config_path=None):
        """
        Interface to load a config file given the config_path attribute, or optional config_path
        argument.

        Returns a dict object.
        """

    def _load_paths(self, filepaths):
        """
        Given a list of filepaths, load each file in the list and return a dictionary that includes
        the parsed contents of the collection of files.
        """

        cfg = {}
        for filepath in filepaths:
            if not os.path.isabs(filepath):
                assert self.config_path is not None
                filepath = os.path.join(os.path.dirname(self.config_path), filepath)
            cfg.update(self._load(config_path=filepath))
        return cfg

    # Public methods

    def compare_config(self, user_dict, base_dict=None):
        """
        Assuming a section, key/value structure of configuration types, compare the dictionary to
        the values stored in the external file.
        """
        if base_dict is None:
            base_dict = self.data

        diffs: dict = {}
        for sect, items in base_dict.items():
            for key, val in items.items():
                if val != user_dict.get(sect, {}).get(key, ""):
                    try:
                        diffs[sect][key] = f" - {val} + {user_dict.get(sect, {}).get(key)}"
                    except KeyError:
                        diffs[sect] = {}
                        diffs[sect][key] = f" - {val} + {user_dict.get(sect, {}).get(key)}"

        for sect, items in user_dict.items():
            for key, val in items.items():
                if (
                    val != base_dict.get(sect, {}).get(key, "")
                    and diffs.get(sect, {}).get(key) is None
                ):
                    try:
                        diffs[sect][key] = f" - {base_dict.get(sect, {}).get(key)} + {val}"
                    except KeyError:
                        diffs[sect] = {}
                        diffs[sect][key] = f" - {base_dict.get(sect, {}).get(key)} + {val}"

        for sect, keys in diffs.items():
            for key in keys:
                msg = f"{sect}: {key:>15}: {keys[key]}"
                self.log.info(msg)

    def dereference(
        self, ref_dict: Optional[dict] = None, full_dict: Optional[dict] = None
    ) -> None:
        """
        This method will be used as a method by which any Config object can cycle through its
        key/value pairs recursively, replacing Jinja2 templates as necessary.
        """

        if ref_dict is None:
            ref_dict = self.data

        if full_dict is None:
            full_dict = self.data

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

    def dereference_all(self):
        """
        Run dereference until all values have been filled in.
        """

        prev = copy.deepcopy(self.data)
        self.dereference()
        while prev != self.data:
            self.dereference()
            prev = copy.deepcopy(self.data)

    def dictionary_depth(self, config_dict):
        """
        Recursively finds the depth of an objects data (a dictionary).
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
        Recursively parse which keys in the object are complete (set_var), which keys have unfilled
        jinja templates (jinja2_var), and which keys are set to empty (empty_var).
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
    def dump_file(self, output_path):
        """
        Interface to write a config object to a file at the output_path provided.
        """

    def from_ordereddict(self, in_dict: dict) -> dict:
        """
        Given a dictionary, replace all instances of OrderedDict with a regular dictionary.
        """
        if isinstance(in_dict, OrderedDict):
            in_dict = dict(in_dict)
        for sect, keys in in_dict.items():
            if isinstance(keys, OrderedDict):
                in_dict[sect] = dict(keys)
        return in_dict

    def parse_include(self, ref_dict=None):
        """
        Assuming a section, key/value structure of configuration types (other than YAML, which
        handles this in its own loader), update the dictionary with the values stored in the
        external file.

        Recursively traverse the stored dictionary, finding any !INCLUDE tags. Update the dictionary
        with the contents of the files to be included.
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
    def str_to_type(self, str_: str) -> Union[bool, float, int, str]:
        """
        Check if the string contains a float, int, boolean, or just regular string.

        This will be used to automatically convert environment variables to data types that are more
        convenient to work with.
        """

        str_ = str_.strip("\"'")
        if str_.lower() in ["true", "yes", "yeah"]:
            return True
        if str_.lower() in ["false", "no", "nope"]:
            return False
        # int
        try:
            return int(str_)
        except ValueError:
            pass
        # float
        try:
            return float(str_)
        except ValueError:
            pass
        return str_

    def update_values(self, new_dict, dict_to_update=None):
        """
        Update the values stored in the class's data (a dict) with the values provided by the new
        dict.
        """

        if dict_to_update is None:
            dict_to_update = self.data

        for key, new_val in new_dict.items():
            if isinstance(new_val, dict):
                if isinstance(dict_to_update.get(key), dict):
                    self.update_values(new_val, dict_to_update[key])
                else:
                    dict_to_update[key] = new_val
            else:
                dict_to_update[key] = new_val


class F90Config(Config):
    """
    Concrete class to handle Fortran namelist files.
    """

    def __init__(self, config_path: Optional[str] = None, log_name: Optional[str] = None) -> None:
        """
        Load the file and update the dictionary.
        """
        super().__init__(config_path, log_name)

        if config_path is not None:
            self.update(self._load())
            self.parse_include()

    # Private methods

    def _load(self, config_path: Optional[str] = None) -> dict:
        """
        Load the user-provided Fortran namelist path into a dict object.
        """
        config_path = config_path or self.config_path
        assert config_path is not None
        with open(config_path, "r", encoding="utf-8") as f:
            cfg = f90nml.read(f).todict(complex_tuple=False)
        return self.from_ordereddict(cfg)

    # Public methods

    def dump_file(self, output_path):
        """
        Write the dict to a namelist file.
        """
        nml = OrderedDict(self.data)
        for sect, keys in nml.items():
            if isinstance(keys, dict):
                nml[sect] = OrderedDict(keys)

        with open(output_path, "w", encoding="utf-8") as file_name:
            f90nml.Namelist(nml).write(file_name, sort=False)


class INIConfig(Config):
    """
    Concrete class to handle INI config files.
    """

    def __init__(
        self,
        config_path: Optional[str] = None,
        log_name: Optional[str] = None,
        space_around_delimiters: bool = True,
    ):
        """
        Load the file and update the dictionary.

        Parameters
        ----------
        space_around_delimiters
            Should be True for INI format, False for bash
        """
        super().__init__(config_path, log_name)
        self.space_around_delimiters = space_around_delimiters

        if config_path is not None:
            self.update(self._load())
            self.parse_include()

    # Private methods

    def _load(self, config_path=None):
        """
        Load the user-provided INI config file path into a dict object.
        """

        config_path = config_path or self.config_path

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

    def dump_file(self, output_path):
        """
        Write the dict to an INI file.
        """

        parser = configparser.ConfigParser()

        with open(output_path, "w", encoding="utf-8") as file_name:
            try:
                parser.read_dict(self.data)
                parser.write(file_name, space_around_delimiters=self.space_around_delimiters)
            except AttributeError:
                for key, value in self.data.items():
                    file_name.write(f"{key}={value}\n")


class YAMLConfig(Config):
    """
    Concrete class to handle YAML configure files.

    Attributes
    ----------

    _yaml_loader : Loader
        The PyYAML Loader that's been extended with constructors

    Methods
    -------

    _yaml_include()
        Static method used to define a constructor function for PyYAML.
    """

    def __init__(self, config_path: Optional[str] = None, log_name: Optional[str] = None) -> None:
        """
        Load the file and update the dictionary.
        """

        super().__init__(config_path, log_name)

        if config_path is not None:
            self.update(self._load())

    def __repr__(self):
        """
        This method will return configure contents.
        """
        return yaml.dump(self.data)

    # Private methods

    def _load(self, config_path=None):
        """
        Load the user-provided YAML config file path into a dict object.
        """

        loader = self._yaml_loader
        config_path = config_path or self.config_path
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

    def _yaml_include(self, loader, node):
        """
        Returns a dictionary that includes the contents of the referenced YAML files, and is used as
        a contructor method for PyYAML.
        """

        filepaths = loader.construct_sequence(node)
        return self._load_paths(filepaths)

    @property
    def _yaml_loader(self):
        """
        Set up the loader with the appropriate constructors.
        """
        loader = yaml.SafeLoader
        loader.add_constructor("!INCLUDE", self._yaml_include)
        return loader

    # Public methods

    def dump_file(self, output_path):
        """
        Write the dictionary to a YAML file.
        """

        with open(output_path, "w", encoding="utf-8") as file_name:
            yaml.dump(self.data, file_name, sort_keys=False)


class FieldTableConfig(YAMLConfig):
    """
    This class exists to write out a field_table format given that its configuration has been set by
    an input YAML file.
    """

    def __init__(self, config_path: Optional[str] = None, log_name: Optional[str] = None) -> None:
        """
        Load the file and update the dictionary.
        """
        super().__init__(config_path, log_name)

        if config_path is not None:
            self.update(self._load())

    # Private methods

    def _format_output(self):
        """
        Format the output of the dictionary into a string that matches that necessary for a
        field_table.

        Return the string.
        """

        outstring = []
        for field, settings in self.data.items():
            outstring.append(f' "TRACER", "atmos_mod", "{field}"')
            for key, value in settings.items():
                if isinstance(value, dict):
                    method_string = f'{" ":7}"{key}", "{value.pop("name")}"'
                    # All control vars go into one set of quotes.
                    control_vars = [f"{method}={val}" for method, val in value.items()]
                    # Whitespace after the comma matters.
                    outstring.append(f'{method_string}, "{", ".join(control_vars)}"')
                else:
                    # Formatting of variable spacing dependent on key length.
                    outstring.append(f'{" ":11}"{key}", "{value}"')
            outstring[-1] += " /"
        return "\n".join(outstring)

    # Public methods

    def dump_file(self, output_path):
        """
        Write the formatted output to a text file. FMS field and tracer managers must be registered
        in an ASCII table called 'field_table'. This table lists field type, target model and
        methods the querying model will ask for.

        See UFS documentation for more information:
        https://ufs-weather-model.readthedocs.io/en/ufs-v1.0.0/InputsOutputs.html#field-table-file

        The example format for generating a field file is:

        sphum:
          longname: specific humidity
          units: kg/kg
          profile_type:
            name: fixed
            surface_value: 1.e30
        """

        with open(output_path, "w", encoding="utf-8") as file_name:
            file_name.write(self._format_output())


def create_config_obj(user_args, log=None):
    """
    Main section for processing config file.
    """

    if log is None:
        name = f"{inspect.stack()[0][3]}"
        log = cli_helpers.setup_logging(
            log_file=user_args.log_file,
            log_name=name,
            quiet=user_args.quiet,
            verbose=user_args.verbose,
        )

    infile_type = user_args.input_file_type or cli_helpers.get_file_type(user_args.input_base_file)

    config_class = globals()[f"{infile_type}Config"]
    config_obj = config_class(user_args.input_base_file, log_name=log.name)

    if user_args.config_file:
        config_file_type = user_args.config_file_type or cli_helpers.get_file_type(
            user_args.config_file
        )

        user_config_obj = globals()[f"{config_file_type}Config"](user_args.config_file)

        if config_file_type != infile_type:
            config_depth = user_config_obj.dictionary_depth(user_config_obj.data)
            input_depth = config_obj.dictionary_depth(config_obj.data)

            if input_depth < config_depth:
                log.critical(f"{user_args.config_file} not compatible with input file")
                raise ValueError("Set config failure: config object not compatible with input file")

        if user_args.compare:
            log.info(f"- {user_args.input_base_file}")
            log.info(f"+ {user_args.config_file}")
            log.info("-" * 80)
            config_obj.compare_config(user_config_obj)
            return

        config_obj.update_values(user_config_obj)

    config_obj.dereference_all()

    if user_args.values_needed:
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

    if user_args.dry_run:
        # Apply switch to allow user to view the results of config instead of writing to disk.
        log.info(config_obj)
        return

    if user_args.outfile:
        outfile_type = user_args.output_file_type or cli_helpers.get_file_type(user_args.outfile)

        if outfile_type != infile_type:
            out_object = globals()[f"{outfile_type}Config"]()
            out_object.update(config_obj)

            # output_depth = out_object.dictionary_depth(out_object.data)
            input_depth = config_obj.dictionary_depth(config_obj.data)

            # Check for incompatible conversion objects.

            err_msg = "Set config failure: incompatible file types"
            if (outfile_type == "INI" and input_depth > 2) or (
                outfile_type == "F90" and input_depth != 2
            ):
                log.critical(err_msg)
                raise ValueError(err_msg)

        else:  # same type of file as input, no need to convert it
            out_object = config_obj
        out_object.dump_file(user_args.outfile)

    if user_args.show_format:
        if outfile_type != infile_type:
            help(out_object.dump_file)
