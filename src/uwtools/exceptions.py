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
