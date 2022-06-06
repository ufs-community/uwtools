import os
from pathlib import PurePath
from ..logger import SilentLogger
from ..file_manager import FileManager
from .base import Base


class Directory(Base):
    """
        Finds files from a source directory and can execute an action to a target directory
        (copy, symlink, etc..) The dictionary expected (data) is as follows:
            directories:  # list pairs (lists or tuple)
                - [source1, target1]
                - [source2, target2]
                - ...
                - [sourceN, targetN]
            exclude:
                - filename1
                - filename2
                - ...
                - filenameN
        Copies all files in sourceN into destinationN skipping filenames in excludes. If targetN
        ends with slash ("/"), it means it's a directory and it is created if necessary, if not,
        it's a file. Forgetting the ending / may result in several files copied on top of each other.
    """

    def __call__(self, data, source, target, logger=SilentLogger()):
        """
           source and target are the root directories, if specified, the directories
           in data are considered to be relative to those.
        """
        exclude = set(data.get('exclude', []))
        count = 0
        for file_group in data['directories']:
            source_dir = os.path.join(source, file_group[0])
            target_dir = os.path.join(target, file_group[1])
            root = self.find_root(source_dir)
            if root == source_dir:
                if os.path.basename(source_dir) not in exclude:
                    filename = ''
                    if target_dir[-1] == '/':
                        FileManager.makedirs(target_dir, exist_ok=True)
                    else:
                        filename = os.path.basename(target_dir)
                        target_dir = os.path.dirname(target_dir)
                    self.action(source_dir, target_dir, filename, logger)
                    count += 1
            else:
                for root, path, filename in FileManager.tree(root):
                    if filename not in exclude:
                        p = os.path.join(root, path, filename)
                        if PurePath(p).match(source_dir):
                            self.action(p, target_dir, filename, logger)
                            count += 1
            plural = ''
            if count:
                plural = 's'
            logger.info(f'{count} file{plural} processed')

    def action(self, source, target_path, target_file, logger):
        raise NotImplementedError('directory base class')
