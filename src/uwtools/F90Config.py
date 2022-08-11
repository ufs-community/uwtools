# pylint: disable=locally-disabled, invalid-name
''' f90nml support instantiated from the Config Abstract Base Class'''
from pathlib import PurePath

import f90nml

from uwtools.config import Config
from uwtools.YAMLConfig import YAMLConfig

class F90Config(Config):
    ''' f90nml support instantiated from the Config Abstract Base Class'''
    def __init__(self, config_file=None,data=None,
                       from_environment=None, replace_realtime=None):
        super().__init__()
        self.f90nmlParser = f90nml.Parser()
        if config_file is not None:
            self._load_file(config_file,data,from_environment,replace_realtime)
            self.config_path = config_file
        else:
            self._load_file(config_file,data, from_environment,replace_realtime)

    #pylint: disable=arguments-differ
    def _load_file(self,config_file,data,from_environment,replace_realtime):
        if config_file is not None:
            self.config_obj = YAMLConfig( config_file,data,
                                          from_environment,
                                          replace_realtime)
            self.config_path = config_file
        else:
            self.config_obj = None
        if data is not None:
            self.config_obj = self.f90nmlParser.reads(data)
        return self.config_obj

    def config_path(self):
        self.config_path = self.config_file
        return self.config_path

    def config_obj(self):
        return self.config_obj

    def dump_file(self, outputpath):
        if self.config_obj is not None:
            with open(PurePath(outputpath), 'w+', encoding='utf-8') as __file:
                f90nml.write(self.config_obj, __file)
