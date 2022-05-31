# pylint: disable=too-few-public-methods, unused-variable

import os
from abc import ABC, abstractmethod
import pathlib
from typing import Any, List

from uwtools.files.gateway import s3, unix
from uwtools.files.model import File, Prefixes, Unix, S3


class FileManager(ABC):
    """represents file operations in an environment"""

    @abstractmethod
    def copy(self, source: List[File], destination: List[File]):
        """copies source to destination"""
        raise NotImplementedError

    @classmethod
    def get_file_manager(cls, _type: Prefixes):
        """returns a file manager with source and destination"""
        _map = {
            Prefixes.UNIX: UnixFileManager,
            Prefixes.S3: S3FileManager,
        }
        return _map[_type]()


class S3FileManager(FileManager):
    """S3 based file operations"""

    def copy(self, source: List[Any], destination: List[S3]):
        """copies source to destination"""
        for (src, dest) in zip(source, destination):
            s3.upload_file(src.path, "bucket_name_here", os.path.basename(dest.path))


class UnixFileManager(FileManager):
    """unix based file operations"""

    def copy(self, source: List[File], destination: List[str]):
        unix.copy(list(source), [pathlib.Path(x) for x in list(destination)])
