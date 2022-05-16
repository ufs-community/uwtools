from abc import ABC, abstractmethod
from enum import Enum
import os
import re
from typing import Any, List


class Prefixes(Enum):
    """represents file prefixes"""

    UNIX = "file://"
    S3 = "s3://"


PREFIX_PATTERN = r"\S.*:\/\/"


class File(ABC):
    """represents a file"""

    def __init__(self, path: str):
        self._path = path
        self.validate()

    def __str__(self) -> str:
        return self._path

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} {self._path}/>"

    def validate(self) -> None:
        """validates the File"""
        # TODO this path and prefix validation is weird
        self.path
        self.prefix
        if not self.exists:
            raise FileNotFoundError(f"File not found [{self._path}]")

    @property
    def prefix(self) -> Prefixes:
        """returns the prefix"""
        result = re.match(PREFIX_PATTERN, self._path)
        prefix = None if result is None else result.group(0)

        if prefix is None:
            raise AttributeError(f"prefix not found in: [{self._path}]")
        if prefix.lower() not in [prefix.value for prefix in Prefixes]:
            raise AttributeError(f"attribute unknown: [{prefix}]")
        return Prefixes(prefix.lower())

    @property
    def path(self) -> str:
        """returns the file path"""
        try:
            return self._path.split("://", maxsplit=1)[1]
        except IndexError:
            return ""

    @property
    @abstractmethod
    def exists(self):
        """returns true if the file exists"""
        raise NotImplementedError

    @property
    @abstractmethod
    def dir(self) -> List[Any]:
        """returns the contents of the directory recursively"""
        raise NotImplementedError


class S3(File):
    """represents an Amazon S3 file"""

    @property
    def exists(self):
        """returns true if the file exists"""
        return True

    @property
    def dir(self) -> List[Any]:
        """returns the contents of the directory recursively"""
        raise NotImplementedError


class Unix(File):
    """represents a unix file"""

    @property
    def exists(self):
        """returns true if the file exists"""
        return os.path.exists(self.path)

    @property
    def dir(self) -> List[Any]:
        """returns the contents of the directory recursively"""
        raise NotImplementedError
