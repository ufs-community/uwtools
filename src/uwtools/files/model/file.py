from abc import ABC, abstractmethod
from enum import Enum
from glob import glob
from pathlib import Path
from typing import Any, List


class Prefixes(Enum):
    """
    Supported URI file prefixes.
    """

    S3 = "s3://"
    UNIX = "file://"


class File(ABC):
    """
    Represents a file.
    """

    def __init__(self, uri: str):
        self._uri = uri
        if not isinstance(self._uri, str):
            raise TypeError("Argument 'uri' must be type str but is type %s" % type(self._uri))
        if not self._uri.startswith(self.uri_prefix):
            raise ValueError(
                "Path %s does not start with expected URI prefix %s" % (self._uri, self.uri_prefix)
            )
        if not self.exists:
            raise FileNotFoundError("File not found: %s" % self._uri)

    def __str__(self) -> str:
        return self._uri

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} {self._uri}/>"

    @property
    def path(self) -> str:
        """
        Returns the file path without a prefix.
        """
        return self._uri.split("://", maxsplit=1)[1]

    @property
    @abstractmethod  # pragma: no cover
    def dir(self) -> List[Any]:
        """
        Returns the contents of the directory recursively.
        """
        raise NotImplementedError()

    @property
    @abstractmethod  # pragma: no cover
    def exists(self) -> bool:
        """
        Returns true if the file exists.
        """
        raise NotImplementedError()

    @property
    @abstractmethod  # pragma: no cover
    def uri_prefix(self) -> str:
        """
        The URI prefix for this file type.
        """
        raise NotImplementedError()


class S3(File):
    """
    Represents an AWS S3 file.
    """

    @property
    def dir(self) -> List[Any]:
        """
        Returns the contents of the directory recursively.
        """
        return []

    @property
    def exists(self) -> bool:
        """
        Returns true if the file exists.
        """
        return True

    @property
    def uri_prefix(self) -> str:
        """
        The URI prefix for this file type.
        """
        return Prefixes.S3.value


class Unix(File):
    """
    Represents a Unix file.
    """

    @property
    def dir(self) -> List[Any]:
        """
        Returns the contents of the directory recursively.
        """
        if Path(self.path).is_file():
            return glob(self.path)
        return glob(str(Path(self.path) / "*"))

    @property
    def exists(self) -> bool:
        """
        Returns true if the file exists.
        """
        return Path(self.path).exists()

    @property
    def uri_prefix(self) -> str:
        """
        The URI prefix for this file type.
        """
        return Prefixes.UNIX.value
