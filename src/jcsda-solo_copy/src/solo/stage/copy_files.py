import os
from ..file_manager import FileManager
from .directory import Directory


class CopyFiles(Directory):

    """
        Please see directory.py for syntax
    """

    def action(self, source, target_path, target_file, logger):
        target = os.path.join(target_path, target_file)
        logger.info(f'Copying {source} to {target}')
        FileManager.copy(source, target)
