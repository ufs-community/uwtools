import sys
from pathlib import Path
import logging

__all__ = ['Logger']


class ColoredFormatter(logging.Formatter):
    '''
    Logging colored formatter
    adapted from https://stackoverflow.com/a/56944256/3638629
    '''

    grey = '\x1b[38;21m'
    blue = '\x1b[38;5;39m'
    yellow = '\x1b[38;5;226m'
    red = '\x1b[38;5;196m'
    bold_red = '\x1b[31;1m'
    reset = '\x1b[0m'

    def __init__(self, fmt):
        super().__init__()
        self.fmt = fmt
        self.FORMATS = {
            logging.DEBUG: self.blue + self.fmt + self.reset,
            logging.INFO: self.grey + self.fmt + self.reset,
            logging.WARNING: self.yellow + self.fmt + self.reset,
            logging.ERROR: self.red + self.fmt + self.reset,
            logging.CRITICAL: self.bold_red + self.fmt + self.reset
        }

    def format(self, record):
        log_fmt = self.FORMATS.get(record.levelno)
        formatter = logging.Formatter(log_fmt)
        return formatter.format(record)


class Logger:

    '''
    Improved logging
    '''

    __all__ = ['get_logger']

    LOG_LEVELS = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
    DEFAULT_LOG_LEVEL = 'INFO'
    FORMAT = '%(asctime)s [%(levelname)s] - %(name)s: %(message)s'

    def __init__(self, name, level=DEFAULT_LOG_LEVEL, logfile_path=None, *args):
        '''
        Constructor for Logger
        '''

        self.name = name
        self.level = level.upper()

        if self.level not in Logger.LOG_LEVELS:
            raise LookupError('{self.level} is unknown logging level\n' +
                              'Currently supported log levels are:\n' +
                              f'{" | ".join(Logger.LOG_LEVELS)}')

        self._logger = logging.getLogger(name)

        self._logger.setLevel(self.level)

        # Create console handler for logger
        ch = self.console_handler()
        self._logger.addHandler(ch)

        # Create file handler for logger
        if logfile_path is not None:
            self.logfile_path = Path(logfile_path)
            fh = self.file_handler()
            self._logger.addHandler(fh)

    def __getattr__(self, attribute):
        '''
        Allows calling logging module methods directly
        '''
        return getattr(self._logger, attribute)

    def get_logger(self):
        '''
        Return the logging object
        '''
        return self._logger

    def console_handler(self):
        '''
        Create console handler for Logger with Colored output
        '''

        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(self.level)
        handler.setFormatter(ColoredFormatter(Logger.FORMAT))

        return handler

    def file_handler(self):
        '''
        Create file handler for Logger with standard output
        '''

        # Create the directory containing the logfile_path
        if not self.logfile_path.parent.is_dir():
            self.logfile_path.mkdir(parents=True, exist_ok=True)

        handler = logging.FileHandler(str(self.logfile_path))
        handler.setLevel(self.level)
        handler.setFormatter(logging.Formatter(Logger.FORMAT))

        return handler
