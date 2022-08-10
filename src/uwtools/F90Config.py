from pathlib import PurePath

import f90nml
import yaml

from uwtools.config import Config
from uwtools.YAMLConfig import YAMLConfig

class F90Config(Config):

    def __init__(self, config_file=None,data=None,
                       from_environment=None, replace_realtime=None):
        super().__init__()
        self.f90nmlParser = f90nml.Parser()
        if config_file is not None:
            self._load_file(config_file=PurePath(config_file),data=None,
                            from_environment=from_environment,
                            replace_realtime=replace_realtime)
            self.config_path(self)
        else:
            self._load_file(config_file=None,data=data,
                            from_environment=from_environment,
                            replace_realtime=replace_realtime)

    def _load_file(self,config_file=None,data=None,
                   from_environment=None,replace_realtime=None):
        if config_file is not None:
            self.config_obj = YAMLConfig( config_file=None,data=data,
                                          from_environment=from_environment,
                                          replace_realtime=replace_realtime)
        else:
            self.config_obj = None
        if data is not None:
            self.config_obj = self.f90nmlParser.reads(data)
        return self.config_obj
    
    def config_path(self):
        self.config_path = self.config_file
        return self.config_pah

    def config_obj(self):
        return self.config_obj

    def dump_file(self, outputpath):
        if self.config_obj is not None:
            with open(PurePath(outputpath), 'w+', encoding='utf-8') as __file:
                f90nml.write(self.config_obj, __file)