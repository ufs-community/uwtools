"""
Logger
"""

import sys
import os
from pathlib import Path
from typing import Union, List
import logging
import functools
from inspect import getframeinfo, stack


class ColoredFormatter(logging.Formatter):
    """
    Logging colored formatter
    adapted from https://stackoverflow.com/a/56944256/3638629
    """

    grey = '\x1b[38;21m'
    blue = '\x1b[38;5;39m'
    yellow = '\x1b[38;5;226m'
    red = '\x1b[38;5;196m'
    bold_red = '\x1b[31;1m'
    reset = '\x1b[0m'

    def __init__(self, fmt):
        super().__init__()
        self.fmt = fmt
        self.formats = {
            logging.DEBUG: self.blue + self.fmt + self.reset,
            logging.INFO: self.grey + self.fmt + self.reset,
            logging.WARNING: self.yellow + self.fmt + self.reset,
            logging.ERROR: self.red + self.fmt + self.reset,
            logging.CRITICAL: self.bold_red + self.fmt + self.reset
        }

    def format(self, record):
        log_fmt = self.formats.get(record.levelno)
        formatter = logging.Formatter(log_fmt)
        return formatter.format(record)


class Logger:
    """
    Improved logging
    """
    LOG_LEVELS = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
    DEFAULT_LEVEL = 'INFO'
    DEFAULT_FORMAT = '%(asctime)s - %(levelname)-8s - %(name)-12s: %(message)s'
    def __init__(self, name: str = None,
                 level: str = DEFAULT_LEVEL,
                 _format: str = DEFAULT_FORMAT,
                 colored_log: bool = False,
                 logfile_path: Union[str, Path] = None):
        """
        Constructor for Logger
        """

        self.name = name
        self.level = level.upper()
        self.format = _format
        self.colored_log = colored_log

        if self.level not in Logger.LOG_LEVELS:
            raise LookupError('{self.level} is unknown logging level\n' +
                              'Currently supported log levels are:\n' +
                              f'{" | ".join(Logger.LOG_LEVELS)}')

        # Initialize the root logger if no name is present
        self._logger = logging.getLogger(name) if name else logging.getLogger()

        self._logger.setLevel(self.level)

        _handlers = []
        # Add console handler for logger
        _handler = Logger.add_stream_handler(
            level=self.level,
            _format=self.format,
            colored_log=self.colored_log,
            )
        _handlers.append(_handler)
        self._logger.addHandler(_handler)

        # Add file handler for logger
        if logfile_path is not None:
            _handler = Logger.add_file_handler(logfile_path, level=self.level, _format=self.format)
            self._logger.addHandler(_handler)
            _handlers.append(_handler)

    def __getattr__(self, attribute):
        """
        Allows calling logging module methods directly
        """
        return getattr(self._logger, attribute)

    def get_logger(self):
        '''
        Return the logging object
        '''
        return self._logger

    @classmethod
    def add_handlers(cls, logger: logging.Logger, handlers: List[logging.Handler]):
        """
        Add a list of handlers to a logger
        Parameters
        ----------
        logger
        handlers

        Returns
        -------
        logger
        """
        for handler in handlers:
            logger.addHandler(handler)

        return logger

    @classmethod
    def add_stream_handler(cls, level: str = DEFAULT_LEVEL,
                            _format: str = DEFAULT_FORMAT,
                            colored_log: bool = False):
        """
        Create stream handler
        This classmethod will allow setting a custom stream handler on children
        """

        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(level)
        _format = ColoredFormatter(_format) if colored_log else logging.Formatter(_format)
        handler.setFormatter(_format)

        return handler

    @classmethod
    def add_file_handler(cls, logfile_path: Union[str, Path],
                         level: str = DEFAULT_LEVEL,
                         _format: str = DEFAULT_FORMAT):
        """
        Create file handler.
        This classmethod will allow setting custom file handler on children
        """

        logfile_path = Path(logfile_path)

        # Create the directory containing the logfile_path
        if not logfile_path.parent.is_dir():
            logfile_path.mkdir(parents=True, exist_ok=True)

        handler = logging.FileHandler(str(logfile_path))
        handler.setLevel(level)
        handler.setFormatter(logging.Formatter(_format))

        return handler

    def log_decorator(self, _func=None):
        """
        Add a logger decorator.
        This decorator will allow setting custom logging details on a given function
        Decorator based on work by Hima Mahajan https://github.com/hima03/log-decorator
        """
        def log_decorator_info(func):
            @functools.wraps(func)
            def log_decorator_wrapper(self, *args, **kwargs):
                #Build logger object
                logger_obj = Logger.get_logger(self)

                # Create a list of the positional arguments passed to function.
                # Using repr() for string representation for each argument. repr() is similar to str() with the only
                # difference being it prints with a pair of quotes and if we calculate a value we get more
                # precise value than str().
                args_passed_in_function = [repr(a) for a in args]
                # Create a list of the keyword arguments. The f-string formats each argument as key=value, where the !r
                # specifier means that repr() is used to represent the value.
                kwargs_passed_in_function = [f"{k}={v!r}" for k, v in kwargs.items()]

                # The lists of positional and keyword arguments is joined together to form final string
                formatted_arguments = ", ".join(args_passed_in_function + kwargs_passed_in_function)

                # Generate file name and function name for calling function. __func.name__ will give the name of the
                # caller function ie. wrapper_log_info and caller file name ie log-decorator.py
                #- In order to get actual function and file name we will use 'extra' parameter.
                #- To get the file name, we are using in-built module inspect.getframeinfo which returns
                # calling file name
                py_file_caller = getframeinfo(stack()[1][0])
                extra_args = { 'func_name_override': func.__name__,
                           'file_name_override': os.path.basename(py_file_caller.filename) }

                # Before the function execution, log function details."""
                logger_obj.info(f"Arguments: {formatted_arguments} - Begin function")
                try:
                    #log return value from the function
                    value = func(self, *args, **kwargs)
                    logger_obj.info(f"Returned: - End function {value!r}", extra=extra_args)
                except:
                    #log exception if occurs in function
                    logger_obj.error(f"Exception: {str(sys.exc_info()[1])}", extra=extra_args)
                    raise
                return value
            return log_decorator_wrapper
        return log_decorator_info if _func is None else log_decorator_info(_func)
