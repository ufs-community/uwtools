'''
This file contains the Config file and its subclasses for a variety of
dicatable file types. 
'''

import abc
import collections
import configparser

import f90nml
import yaml

from uwtools.yaml_file import Template, TemplateConstants 
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

    '''


    def __init__(self, config_path):

        '''
        Parameters
        ----------
        config_path : Path (See Above)

        '''

        super().__init__()

        self.config_path = config_path

    @abc.abstractmethod
    def _load(self):
        ''' Interface to load a config file given the config_path
        attribute. Returns a dict object. '''

    @abc.abstractmethod
    def dump_file(self, output_path):
        ''' Interface to write a config object to a file at the
        output_path provided. '''

    def parse_include(self):
        '''Borrowing from pyyaml, traverse the dict to treat the
        !INCLUDE  tag just the same as it would be treated in YAML. This
        is left for further exploration and design in PI6, and applies
        to any non-YAML config file types, so putting it in the base
        class for now.'''

    def replace_templates(self):
        ''' This method will be used as a method by which any Config
        object can cycle through its key/value pairs recursively,
        replacing Jinja2 templates as necessary. This is a placeholder
        until more details are fleshed out in work scheduled for PI6.'''


class YAMLConfig(Config):
    '''Class for YAML loader and support for in place value subsitution and include'''

    def __init__(self, config_path):
        ''' Load the file and update the dictionary '''
        super().__init__(config_path)
        self.config_obj = None
        self.update(self._load())

    def _load(self):
        ''' Load the user-provided YAML config file path into a dict object.'''
        with open(self.config_path, 'r', encoding="utf-8") as file_name:
            config = yaml.load(file_name, Loader=yaml.Loader)
            self.config_obj = config
            self.update(config)
        return config

    # This is the overloaded method for UserDict to realize dot notation resolution
    # it has moved this back to a Config class which is now a Abstract Class
    def __getattr__(self, item):
        if item in self:
            return self.__dict__["data"][item]
            #return self[item]
        raise AttributeError(f"'{type(self)}' object has no attribute '{item}'")

    def parse_include(self,config_file=None,data=None,from_environment=None,replace_realtime=None):
        ''' Sample code needed to implement the !INCLUDE tag '''
        if config_file is not None:
            with open(config_file,encoding='utf-8') as _file:
                config = yaml.load(_file, Loader=yaml.Loader)
            self.config_path = config_file
        else:
            config = data
        if from_environment:
            config = Template.substitute_structure_from_environment(config)
        config = Template.substitute_structure(config,TemplateConstants.
                                               DOLLAR_PARENTHESES,self.get)
        if replace_realtime:
            config = Template.substitute_structure(config,
                     TemplateConstants.DOUBLE_CURLY_BRACES,self.get)
        config = Template.substitute_with_dependencies(config,config,
                 TemplateConstants.DOLLAR_PARENTHESES,shallow_precedence=False)
        if config is not None:
            self.update(config)
        self.config_obj = config
        return config

    def dump_file(self, output_path):
        ''' Write the dictionary to a YAML file '''
        with open(output_path, 'w+', encoding="utf-8") as file_name:
            if self.config_obj is not None:
                yaml.dump(self.config_obj, file_name, sort_keys=False)

class F90Config(Config):

    ''' Concrete class to handle Fortran namelist files. '''

    def __init__(self, config_path=None,data=None):
        ''' Load the file and update the dictionary '''
        super().__init__(config_path)
        self.nml_parser = f90nml.Parser()
        self.data = data
        self.config_obj = None
        #self.update(self._load())
        self._load()

    def _load(self):
        ''' Load the user-provided Fortran namelist path into a dict
        object. '''
        if self.data is not None:
            config = self.nml_parser.reads(self.data)
            self.config_obj = config
        elif self.config_path is not None:
            with open(self.config_path, 'r', encoding="utf-8") as file_name:
                config = f90nml.read(file_name).todict(complex_tuple=False)
                self.config_obj = config
        return config

    def dump_file(self, output_path):
        ''' Write the dict to a namelist file. '''
        with open(output_path, 'w+', encoding="utf-8") as file_name:
            f90nml.write(self.config_obj,file_name)
            #f90nml.Namelist(self.data).write(file_name)

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

    def _load(self):
        ''' Load the user-provided INI config file path into a dict
        object. '''

        # The protected _sections method is the most straightroward way to get
        # at the dict representation of the parse config.
        # pylint: disable=protected-access
        cfg = configparser.ConfigParser()
        try:
            cfg.read(self.config_path)
        except configparser.MissingSectionHeaderError:
            with open(self.config_path, 'r', encoding="utf-8") as file_name:
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
