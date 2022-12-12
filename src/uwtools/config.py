'''
This file contains the Config file and its subclasses for a variety of
dicatable file types.
'''

import abc
import collections
import configparser
import copy
import os

import json
import f90nml
import yaml

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

    def __init__(self, config_path):

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

    def replace_templates(self):
        ''' This method will be used as a method by which any Config
        object can cycle through its key/value pairs recursively,
        replacing Jinja2 templates as necessary. This is a placeholder
        until more details are fleshed out in work scheduled for PI6.'''

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

    def __init__(self, config_path):

        ''' Load the file and update the dictionary '''

        super().__init__(config_path)

        self.update(self._load())

    def _load(self, config_path=None):
        ''' Load the user-provided YAML config file path into a dict
        object. '''

        loader = self._yaml_loader
        config_path = config_path or self.config_path
        with open(config_path, 'r', encoding="utf-8") as file_name:
            cfg = yaml.load(file_name, Loader=loader)
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

    def __init__(self, config_path):

        ''' Load the file and update the dictionary '''
        super().__init__(config_path)

        self.update(self._load())
        self.parse_include()

    def _load(self, config_path=None):
        ''' Load the user-provided Fortran namelist path into a dict
        object. '''
        config_path = config_path or self.config_path
        with open(config_path, 'r', encoding="utf-8") as file_name:
            cfg = f90nml.read(file_name)
        return cfg.todict(complex_tuple=False)

    def dump_file(self, output_path):
        ''' Write the dict to a namelist file. '''
        with open(output_path, 'w', encoding="utf-8") as file_name:
            f90nml.Namelist(self.data).write(file_name)

class INIConfig(Config):

    ''' Concrete class to handle INI config files. '''

    def __init__(self, config_path, space_around_delimiters=True):

        ''' Load the file and update the dictionary

        Parameters
        ----------
        space_around_delimiters : bool. True corresponds to INI format,
             while False is necessary for bash configuration files
        '''
        super().__init__(config_path)
        self.space_around_delimiters = space_around_delimiters

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
                return cfg._sections.get('top')

        return cfg._sections

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

    def __init__(self, config_path):

        ''' Load the file and update the dictionary '''
        super().__init__(config_path)

        self.update(self._load())

    def _format_output(self):
        ''' Format the output of the dictionary into a string that
        matches that necessary for a field_table. Return the string'''

    def dump_file(self, output_path):
        ''' Write the formatted output to a text file. '''
        with open(output_path, 'w', encoding="utf-8") as file_name:
            file_name.write(self._format_output())
