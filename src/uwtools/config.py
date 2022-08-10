
from collections import UserDict

from abc import ABC, abstractclassmethod

class Config(ABC, UserDict):

    def __init__(self, config_file=None, data=None, from_environment=True,replace_realtime=False):
        super().__init__()
        self.config_pah = config_file

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
    def _load_file(self, _path=None, data=None, from_environment=True,replace_realtime=False):
        pass

    @abstractclassmethod
    def dump_file(self, _path, data=None):
        pass

    def __replace_templates(self):
        pass
