'''
Class for managing YAML files with inline and envitionmenti
variable substituion with file inclustion support
'''
# (C) Copyright 2020-2022 UCAR
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
#
# Part of this software is developed by the Joint Center for
# Satellite Data Assimilation (JCSDA) together with its partners.

import os

import yaml
from uwtools.config import Config
from uwtools.template import Template, TemplateConstants

class YAMLFile(Config):

    """
        Reads a YAML file as a UserDict and recursively converts
        nested dictionaries into UserDict.
        Provides a way of saving the dictionary issued from the yaml file,
        after modification or not.
    """

    def __init__(self, config_file=None, data=None, from_environment=True,replace_realtime=False):
        super().__init__()
        print('running YAMLFile init')
        print(config_file)
        if config_file is not None:
            config = self._load_file(config_file=os.path.abspath(config_file),data=None,
                                       from_environment=from_environment,
                                       replace_realtime=replace_realtime)
        else:
            config = self._load_file(config_file=None,data=data,
                                     from_environment=from_environment,
                                     replace_realtime=replace_realtime)
        # TODO check this may be redundant
        if config is not None:
            self.config_path = config_file
            self.update(self._configure(config))

    # Moved this back to a Config class which is now a Abstract Class (not sure if that will work)
    #def __getattr__(self, item):
    #    if item in self:
    #        return self.__dict__["data"][item]
    #        #return self[item]
    #    raise AttributeError(f"'{type(self)}' object has no attribute '{item}'")

    def _configure(self, config):
        for key, value in config.items():
            if isinstance(value, dict):
                config[key] = value
                self._configure(value)
            elif isinstance(value, list):
                for i, var in enumerate(value):
                    if isinstance(var, dict):
                        value[i] = var
                        self._configure(var)
        return config

    def _load_file(self,config_file=None,data=None,from_environment=True,replace_realtime=False):
        ''' Sample code needed to implement the !INCLUDE tag '''
        if config_file is not None:
            with open(config_file,encoding='utf-8') as _file:
                config = yaml.load(_file, Loader=yaml.Loader)
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
            self.update(self._configure(config))
        self.config_obj = config   
        return config

    def config_path(self):
        self.config_path = self.config_path

    def config_obj(self):
        self.config_obj = self.config_obj

    def dump_file(self):
        print('write out YAML file')