# pylint: disable=unused-variable,missing-class-docstring,missing-module-docstring
class UWException(Exception):
    pass

class SchedulerError(UWException):
    pass

class FileManagerError(UWException):
    pass

class ConfigManagerError(UWException):
    pass

class DatabaseManagerError(UWException):
    pass
