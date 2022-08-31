'''
This file contains the Config file and its subclasses for a variety of
dicatable file types.
'''
import re
import os
import copy

import abc
import collections
import configparser

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

    '''


    def __init__(self, config_path):

        '''
        Parameters
        ----------
        config_path : Path (See Above)
        '''

        super().__init__()

        self.config_path = config_path

    # Moved back into YAMLConifig to suppor polymorphisms
    #def __getattr__(self, item):
    #    '''overloaded function to UserDict to support dot resolution'''
    #    if item in self:
    #        return self.__dict__["data"][item]
    #        #return self[item]
    #    raise AttributeError(f"'{type(self)}' object has no attribute '{item}'")

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


# (C) Copyright 2020-2022 UCAR
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
#
# Part of this software is developed by the Joint Center for Satellite Data
# Assimilation (JCSDA) together with its partners.

from collections.abc import Sequence
from dataclasses import dataclass
@dataclass
class TemplateConstants:
    '''Supported identifiers for variable substitution'''
    DOLLAR_CURLY_BRACE = '${}'
    DOLLAR_PARENTHESES = '$()'
    DOUBLE_CURLY_BRACES = '{{}}'
    AT_SQUARE_BRACES = '@[]'
    AT_ANGLE_BRACKETS = '@<>'

    SubPair = collections.namedtuple('SubPair', ['regex', 'slice'])
class Template:

    """
        Utility for substituting variables in a template. The template can be the
        contents of a whole file as a string (substitute_string) of in a complex
        dictionary (substitute_structure).  substitutions defines different type
        of variables with a regex and a slice: - the regex is supposed to find the
        whole variable, e.g, $(variable) - the slice indicate how to slice the value
        returned by the regex to have the variable name, in the
          case of $(variable), the slice is 2, -1 to remove $( and ).
        You can easily add new type of variables following those rules.

        Please note that the regexes allow for at least one nested variable and the
        code is able to handle it.  It means that $($(variable)) will be processed
        correctly but the substitutions will need more than one pass.

        If you have a file that is deeper than just a simple dictionary of has lists
        in it, you can use the method build_index to create a dictionary that will
        have all the options from deeper levels (list, dicts).  You can then pass
        index.get as an argument to any method you use.  If you use
        substitute_with_dependencies, this is done automatically.
    """

    substitutions = {
        TemplateConstants.
           DOLLAR_CURLY_BRACE: TemplateConstants.SubPair(re.compile(r'\${.*?}+'), slice(2, -1)),
        TemplateConstants.
           DOLLAR_PARENTHESES: TemplateConstants.SubPair(re.compile(r'\$\(.*?\)+'), slice(2, -1)),
        TemplateConstants.
           DOUBLE_CURLY_BRACES: TemplateConstants.SubPair(re.compile(r'{{.*?}}+'), slice(2, -2)),
        TemplateConstants.
           AT_SQUARE_BRACES: TemplateConstants.SubPair(re.compile(r'@\[.*?\]+'), slice(2, -1)),
        TemplateConstants.
           AT_ANGLE_BRACKETS: TemplateConstants.SubPair(re.compile(r'@\<.*?\>+'), slice(2, -1))
    }

    def is_single_type_or_string(s):
        '''ease of use code encapsulation'''
        # pylint: disable=invalid-name,no-self-argument
        if isinstance(s, str):
            return True
        try:
            len(s)
        except TypeError:
            return True
        else:
            return False

    @classmethod
    def find_variables(cls, variable_to_substitute: str, var_type: str):
        '''look for variables to reslove by searching through supported identifiers'''
        pair = cls.substitutions[var_type]
        return [x[pair.slice] for x in re.findall(pair.regex, variable_to_substitute)]

    @classmethod
    def substitute_string(cls, variable_to_substitute, var_type: str, get_value):
        """
            Substitutes variables under the form var_type (e.g. DOLLAR_CURLY_BRACE),
            looks for a value returned by function get_value and if found, substitutes
            the variable. Convert floats and int to string before substitution.
            If the value in the dictionary is a complex type, just assign it instead
            of substituting.
                get_value is a function that returns the value to substitute:
                signature: get_value(variable_name).
                If substituting from a dictionary my_dict,  pass my_dict.get
        """
        pair = cls.substitutions[var_type]
        #pylint: disable=too-many-nested-blocks
        if isinstance(variable_to_substitute, str):
            #pylint: disable=invalid-name
            variable_names = re.findall(pair.regex, variable_to_substitute)
            for variable in variable_names:
                var = variable[pair.slice]
                v = get_value(var)
                if v is not None:
                    if not cls.is_single_type_or_string(v):
                        if len(variable_names) == 1:
                            # v could be a list or a dictionary
                            # (complex structure and not a string).
                            # If there is one variable that is the whole
                            # string, we can safely replace,
                            # otherwise do nothing.
                            if variable_to_substitute.\
                            replace(variable_names[0][pair.slice], '') == var_type:
                                variable_to_substitute = v
                    else:
                        if isinstance(v, (float, int)):
                            v = str(v)
                        if isinstance(v, str):
                            variable_to_substitute = variable_to_substitute.replace(variable, v)
                        else:
                            variable_to_substitute = v
                else:
                    more = re.search(pair.regex, var)
                    if more is not None:
                        new_value = cls.substitute_string(var, var_type, get_value)
                        variable_to_substitute = variable_to_substitute.replace(var, new_value)
        return variable_to_substitute

    @classmethod
    def substitute_structure(cls, structure_to_substitute, var_type: str, get_value):
        """
            Traverses a dictionary and substitutes variables in fields, lists
            and nested dictionaries.
        """
        if isinstance(structure_to_substitute, dict):
            for key, item in structure_to_substitute.items():
                structure_to_substitute[key] = cls.substitute_structure(item, var_type, get_value)
        elif isinstance(structure_to_substitute, Sequence)\
        and not isinstance(structure_to_substitute,str):
            for i, item in enumerate(structure_to_substitute):
                structure_to_substitute[i] = cls.substitute_structure(item, var_type, get_value)
        else:
            structure_to_substitute = cls.substitute_string(structure_to_substitute, var_type,
                                                            get_value)
        return structure_to_substitute

    @classmethod
    def substitute_structure_from_environment(cls, structure_to_substitute):
        '''get values for keys from system environment vairables'''
        return cls.substitute_structure(structure_to_substitute,
                TemplateConstants.DOLLAR_CURLY_BRACE, os.environ.get)

    @classmethod
    def substitute_with_dependencies(cls, dictionary, keys, var_type: str,
                                     shallow_precedence=True, excluded=()):
        #pylint: disable=too-many-arguments
        """
            Given a dictionary with a complex (deep) structure, we want to substitute variables,
            using keys, another dictionary that may also have a deep structure (dictionary and keys
            can be the same dictionary if you want to substitute in place).
            We create an index based on keys (see build_index) and substitute values in dictionary
            using index. If variables may refer to other variables, more than one pass of
            substitution may be needed, so we substitute until there is no more change
            in dictionary (convergence).
        """
        all_variables = cls.build_index(keys, excluded, shallow_precedence)
        previous = {}
        while dictionary != previous:
            previous = copy.deepcopy(dictionary)
            dictionary = cls.substitute_structure(dictionary, var_type, all_variables.get)
        return dictionary

    @classmethod
    def build_index(cls, dictionary, excluded=None, shallow_precedence=True):
        """
            Builds an index of all keys with their values, going deep into the dictionary. The index
            if a flat structure (dictionary).
            If the same key name is present more than once in the structure, we want to
            either priorities values that are near the root of the tree (shallow_precedence=True)
            or values that are near the leaves (shallow_precedence=False). We don't anticipated use
            cases where the "nearest variable" should be used, but this could constitute a future
            improvement.
        """
        def build(structure, variables):
            if isinstance(structure, dict):
                for k, i in structure.items():
                    if ((k not in variables) or (k in variables and not shallow_precedence))\
                    and k not in excluded:
                        variables[k] = i
                        build(i, variables)
            elif isinstance(structure, Sequence) and not isinstance(structure, str):
                for vrs in structure:
                    build(vrs, variables)
        var = {}
        if excluded is None:
            excluded = set()
        build(dictionary, var)
        return var
