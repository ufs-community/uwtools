'''
This file contains the Config file and its subclasses for a variety of
dicatable file types.
'''

import abc
import collections
import configparser
import copy
import json
import os
import re

import jinja2
import f90nml
import yaml

from uwtools.j2template import J2Template

class Config(collections.UserDict):

    '''
    This base class provides the interface to methods used to read in
    several configuration file types and manipulate them as such.

    Attributes
    ----------

    config_path : Path
        The file path to the configuration file to be parsed.

    Methods
    -------

    _load()
        Abstract method used as an interface to load a config file

    dump_file(output_path)
        Abstract method used as an interface to write a file to disk

    from_ordereddict(in_dict)
        Given a dictionary, replaces instances of OrderedDict with a
        regular dictionary

    parse_include()
        Traverses the dictionary treating the !INCLUDE path the same as
        is done by pyyaml.

    replace_templates()
        Traverses the dictionary and renders any Jinja2 templated
        fields.

    update_values()
        Update the values in an existing dictionary with values provided
        by a second dictionary. Keep any of the values that are not
        present in the second dictionary.
    '''

    def __init__(self, config_path=None):

        '''
        Parameters
        ----------
        config_path : Path (See Above)

        '''

        super().__init__()

        self.config_path = config_path

    def __repr__(self):
        ''' This method will return configure contents'''
        return json.dumps(self.data)

    @abc.abstractmethod
    def _load(self, config_path=None):
        ''' Interface to load a config file given the config_path
        attribute, or optional config_path argument. Returns a dict
        object. '''

    @abc.abstractmethod
    def dump_file(self, output_path):
        ''' Interface to write a config object to a file at the
        output_path provided. '''

    def from_ordereddict(self, in_dict):
        '''
        Given a dictionary, replace all instances of OrderedDict with a
        regular dictionary.
        '''
        if isinstance(in_dict, collections.OrderedDict):
            in_dict = dict(in_dict)

        for sect, keys in in_dict.items():
            if isinstance(keys, collections.OrderedDict):
                in_dict[sect] = dict(keys)

    def _load_paths(self, filepaths):
        '''
        Given a list of filepaths, load each file in the list and return
        a dictionary that includes the parsed contents of the collection
        of files.
        '''

        cfg = {}
        for filepath in filepaths:
            if not os.path.isabs(filepath):
                filepath = os.path.join(os.path.dirname(self.config_path), filepath)
            cfg.update(self._load(config_path=filepath))
        return cfg

    def parse_include(self, ref_dict=None):
        '''
        Assuming a section, key/value structure of configuration types
        (other than YAML, which handles this in its own loader), update
        the dictionary with the values stored in the external file.

        Recursively traverse the stored dictionary, finding any !INCLUDE
        tags. Update the dictionary with the contents of the files to be
        included.
        '''

        if ref_dict is None:
            ref_dict = self.data

        for key, value in copy.deepcopy(ref_dict).items():
            if isinstance(value, dict):
                self.parse_include(ref_dict[key])
            elif isinstance(value, str) and '!INCLUDE' in value:
                filepaths = value.lstrip('!INCLUDE [').rstrip(']').split(',')

                # Update the dictionary with the values in the
                # included file
                self.update_values(self._load_paths(filepaths))
                del ref_dict[key]

    def dereference(self, ref_dict=None, full_dict=None):

        # pylint: disable=too-many-branches

        ''' This method will be used as a method by which any Config
        object can cycle through its key/value pairs recursively,
        replacing Jinja2 templates as necessary.'''

        if ref_dict is None:
            ref_dict = self.data

        if full_dict is None:
            full_dict = self.data

        if not isinstance(ref_dict, dict):
            return

        for key, val in ref_dict.items():

            if isinstance(val, dict):
                self.dereference(val, full_dict)
            else:

                # Save a bit of compute and only do this part for strings that
                # contain the jinja double brackets.
                v_str = str(val)
                is_a_template = any((ele for ele in ["{{", "{%"] if ele in v_str))
                if is_a_template:

                    # Find expressions first, and process them as a single template
                    # if they exist
                    # Find individual double curly brace template in the string
                    # otherwise. We need one substitution template at a time so that
                    # we can opt to leave some un-filled when they are not yet set.
                    # For example, we can save cycle-dependent templates to fill in
                    # at run time.
                    if "{%" in val:
                        # Treat entire line as a single template
                        templates = [v_str]
                    else:
                        # Separate out all the double curly bracket pairs
                        templates = re.findall(r"{{[^}]*}}|\S", v_str)
                    data = []
                    for template in templates:
                        # Creating the config object for the template
                        # like this, gives us access to all the keys in
                        # the current section without the need to
                        # reference the current section name, and to the
                        # other sections with dot values. Also make
                        # environment variables available with env
                        # prefix.
                        if ref_dict == full_dict:
                            config_obj = dict(**os.environ,
                                              **full_dict)
                        else:
                            config_obj = dict(**os.environ,
                                              **ref_dict,
                                              **full_dict)
                        j2tmpl = J2Template(configure_obj=config_obj,
                                            template_str=template,
                                            loader_args=dict(undefined=jinja2.StrictUndefined)
                                            )
                        rendered = template
                        try:
                            # Fill in a template that has the appropriate variables
                            # set.
                            rendered = j2tmpl.render_template()
                        except jinja2.exceptions.UndefinedError:
                            # Leave a templated field as-is in the resulting dict
                            pass
                        except TypeError:
                            pass
                        except ZeroDivisionError:
                            pass
                        except:
                            # Fail on any other exception...something is
                            # probably wrong.
                            print(f"{key}: {template}")
                            raise

                        data.append(rendered)

                    # Put the full template line back together as it was,
                    # filled or not, and make a guess on its intended type.
                    ref_dict[key] = self.str_to_type("".join(data))

    @staticmethod
    def str_to_type(str_):
        ''' Check if the string contains a float, int, boolean, or just
        regular string. This will be used to automatically convert
        environment variables to data types that are more convenient to
        work with.'''


        str_ = str_.strip("\"'")
        if str_.lower() in ["true", "yes", "yeah"]:
            return True
        if str_.lower() in ["false", "no", "nope"]:
            return False
        # int
        try:
            val = int(str_)
            return val
        except ValueError:
            pass
        # float
        try:
            val = float(str_)
            return val
        except ValueError:
            pass
        return str_

    def update_values(self, new_dict, dict_to_update=None):
        '''
        Update the values stored in the class's data (a dict) with
        the values provided by the new_dict.
        '''

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


class YAMLConfig(Config):

    '''
    Concrete class to handle YAML configure files.

    Attributes
    ----------

    _yaml_loader : Loader
        The PyYAML Loader that's been extended with constructors

    Methods
    -------

    _yaml_include()
        Static method used to define a constructor function for PyYAML.

    '''

    def __init__(self, config_path=None):

        ''' Load the file and update the dictionary '''

        super().__init__(config_path)

        if config_path is not None:
            self.update(self._load())

        prev = copy.deepcopy(self.data)
        self.dereference()
        while prev != self.data:
            self.dereference()
            prev = copy.deepcopy(self.data)

    def _load(self, config_path=None):
        ''' Load the user-provided YAML config file path into a dict
        object. '''

        loader = self._yaml_loader
        config_path = config_path or self.config_path
        with open(config_path, 'r', encoding="utf-8") as file_name:
            cfg = yaml.load(file_name, Loader=loader)

        self.from_ordereddict(cfg)
        return cfg

    def dump_file(self, output_path):
        ''' Write the dictionary to a YAML file '''

        with open(output_path, 'w', encoding="utf-8") as file_name:
            yaml.dump(self.data, file_name, sort_keys=False)

    def _yaml_include(self, loader, node):
        ''' Returns a dictionary that includes the contents of the referenced
        YAML files, and is used as a contructor method for PyYAML'''

        filepaths = loader.construct_sequence(node)
        return self._load_paths(filepaths)

    @property
    def _yaml_loader(self):
        ''' Set up the loader with the appropriate constructors. '''
        loader = yaml.SafeLoader
        loader.add_constructor('!INCLUDE', self._yaml_include)
        return loader

class F90Config(Config):

    ''' Concrete class to handle Fortran namelist files. '''

    def __init__(self, config_path=None):

        ''' Load the file and update the dictionary '''
        super().__init__(config_path)

        if config_path is not None:
            self.update(self._load())
            self.parse_include()

    def _load(self, config_path=None):
        ''' Load the user-provided Fortran namelist path into a dict
        object. '''
        config_path = config_path or self.config_path
        with open(config_path, 'r', encoding="utf-8") as file_name:
            cfg = f90nml.read(file_name).todict(complex_tuple=False)

        cfg = dict(cfg)
        self.from_ordereddict(cfg)
        return cfg

    def dump_file(self, output_path):
        ''' Write the dict to a namelist file. '''
        nml = collections.OrderedDict(self.data)
        for sect, keys in nml.items():
            if isinstance(keys, dict):
                nml[sect] = collections.OrderedDict(keys)

        with open(output_path, 'w', encoding="utf-8") as file_name:
            f90nml.Namelist(nml).write(file_name, sort=False)

class INIConfig(Config):

    ''' Concrete class to handle INI config files. '''

    def __init__(self, config_path=None, space_around_delimiters=True):

        ''' Load the file and update the dictionary

        Parameters
        ----------
        space_around_delimiters : bool. True corresponds to INI format,
             while False is necessary for bash configuration files
        '''
        super().__init__(config_path)
        self.space_around_delimiters = space_around_delimiters

        if config_path is not None:
            self.update(self._load())
            self.parse_include()

    def _load(self, config_path=None):
        ''' Load the user-provided INI config file path into a dict
        object. '''

        config_path = config_path or self.config_path

        # The protected _sections method is the most straightroward way to get
        # at the dict representation of the parse config.
        # pylint: disable=protected-access
        cfg = configparser.ConfigParser()
        try:
            cfg.read(config_path)
        except configparser.MissingSectionHeaderError:
            with open(config_path, 'r', encoding="utf-8") as file_name:
                cfg.read_string("[top]\n" + file_name.read())
                ret_cfg = dict(cfg._sections.get('top'))
                self.from_ordereddict(ret_cfg)
                return ret_cfg

        ret_cfg = dict(cfg._sections)
        self.from_ordereddict(ret_cfg)
        return ret_cfg

    def dump_file(self, output_path):

        ''' Write the dict to an INI file '''

        parser = configparser.ConfigParser()

        with open(output_path, 'w', encoding="utf-8") as file_name:
            try:
                parser.read_dict(self.data)
                parser.write(file_name, space_around_delimiters=self.space_around_delimiters)
            except AttributeError:
                for key, value in self.data.items():
                    file_name.write(f'{key}={value}\n')

class FieldTableConfig(YAMLConfig):

    ''' This class will exist only to write out field_table format given
    that its configuration has been set by an input YAML file. '''

    def __init__(self, config_path=None):

        ''' Load the file and update the dictionary '''
        super().__init__(config_path)

        if config_path is not None:
            self.update(self._load())

    def _format_output(self):
        ''' Format the output of the dictionary into a string that
        matches that necessary for a field_table. Return the string'''

    def dump_file(self, output_path):
        ''' Write the formatted output to a text file. '''
        with open(output_path, 'w', encoding="utf-8") as file_name:
            file_name.write(self._format_output())
