#pylint: disable=unused-variable
'''Abstract Base Class for consolidating Configure Classes for each configurable subsystem'''
from collections import UserDict
from abc import ABC, abstractmethod
class Config(ABC, UserDict):
    '''Abstract Base Class for consolidating Configure Classes for each configurable subsystem'''

    def __getattr__(self, item):
        if item in self:
            return self.__dict__["data"][item]
            #return self[item]
        raise AttributeError(f"'{type(self)}' object has no attribute '{item}'")

    #@property TO DO (make a property)
    @abstractmethod
    def config_path(self):
        '''required attribute for path to configure file'''
        return self.config_file

    #@config_path.setter
    #def config_path(self,config_file):
    #    self.config_path = config_file

    @abstractmethod
    def config_obj(self):
        '''required attribute of python obj pointer to how the config file is used'''
        return self.config_obj

    @classmethod
    @abstractmethod
    def _load_file(cls,config_file=None):
        pass

    @classmethod
    @abstractmethod
    def dump_file(cls,outputpath):
        '''required method to same configuration file'''

    def __replace_templates(self): #pylint: disable=unused-private-member
        '''TODO not sure of requirement yet'''
