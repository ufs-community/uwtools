import os
import pathlib
from abc import ABC, abstractmethod
from typing import List

from uwtools.files.gateway import s3, unix
from uwtools.files.model import S3, File, Prefixes


class FileManager(ABC):
    """
    Represents file operations in an environment.
    """

    @abstractmethod  # pragma: no cover
    def copy(self, source: List[File], destination: List):
        """
        Copies source to destination.
        """
        raise NotImplementedError

    @staticmethod
    def get_file_manager(_type: Prefixes):
        """
        Returns a file manager with source and destination.
        """
        _map = {
            Prefixes.UNIX: UnixFileManager,
            Prefixes.S3: S3FileManager,
        }
        return _map[_type]()


class S3FileManager(FileManager):
    """
    S3 based file operations.
    """

    def copy(self, source: List[File], destination: List[S3]):
        """
        Copies source to destination.
        """
        for src, dest in zip(source, destination):
            s3.upload_file(src.path, "bucket_name_here", os.path.basename(dest.path))


class UnixFileManager(FileManager):
    """
    UNIX based file operations.
    """

    def copy(self, source: List[File], destination: List[str]):
        unix.copy(list(source), [pathlib.Path(x) for x in list(destination)])
