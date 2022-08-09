
from collections import UserDict

from abc import ABC, abstractclassmethod
from telnetlib import NOOPT

class ConfigABC(ABC):
    
    @abstractclassmethod
    def _init(self):
        NOOPT

class Config(ConfigABC, UserDict):

    def _init(self, config_file=None, data=None, from_environment=True,replace_realtime=False):
        super().__init()
        super().__init__()
        self.config_path(config_file)

    def __getattr__(self, item):
        if item in self:
            return self.__dict__["data"][item]
            #return self[item]
        raise AttributeError(f"'{type(self)}' object has no attribute '{item}'")

    @property
    @abstractclassmethod
    def config_path(self):
        pass

    @property
    @abstractclassmethod
    def config_obj(self):
        pass

    @abstractclassmethod
    def _load_file(self, _path=None, data=None):
        pass

    @abstractclassmethod
    def dump_file(self, _path, data=None):
        pass

    def __replace_templates(self):
        pass
