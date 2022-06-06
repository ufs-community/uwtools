import sys
import os
import logging


class Logger:
    """
        class for logging, can be way improved.
    """

    FORMAT = '%(asctime)s - %(levelname)s - %(name)s - %(message)s'

    def __init__(self, name, *args, silent=False):
        # *args can be a list of handlers added to the console
        self._logger = logging.getLogger(name)
        if silent:
            handler = logging.NullHandler()
        else:
            handler = logging.StreamHandler(sys.stdout)
            handler.setFormatter(logging.Formatter(self.FORMAT))
        self._logger.addHandler(handler)
        for handler in args:
            self._logger.addHandler(handler)
        level = os.environ.get('LOG_LEVEL', 'DEBUG')
        self._logger.setLevel(getattr(logging, level))
        self._logger.propagate = False

    def __getattr__(self, attribute):
        return getattr(self._logger, attribute)

    def use_file_logging(self, log_file_path: str):
        for handler in self._logger.handlers:
            self._logger.removeHandler(handler)
        handler = logging.FileHandler(log_file_path)
        handler.setFormatter(logging.Formatter(self.FORMAT))
        self._logger.addHandler(handler)


class SilentLogger:
    """
        True logger that does not output anything
    """

    def __new__(cls, *args, **kwargs):
        return Logger('', silent=True)
