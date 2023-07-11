"""
Unix-based, threaded, local file copying.
"""

import logging
import shutil
from concurrent.futures import ThreadPoolExecutor, wait
from pathlib import Path
from typing import List, Tuple

from uwtools.files.model import File


class Copier:
    """
    A threaded file copier.
    """

    def __init__(self, srcs: List[File], dsts: List[Path]) -> None:
        self.pairs: List[Tuple[Path, Path]] = list(zip([Path(x.path) for x in srcs], dsts))

    def run(self) -> None:
        """
        Copy each src->dst pair in a thread.
        """
        executor = ThreadPoolExecutor()
        futures = [executor.submit(_copy, src, dst) for src, dst in self.pairs]
        wait(futures)


def copy(srcs: List[File], dsts: List[Path]) -> None:
    """
    Copies each source item to corresponding destination item.
    """
    Copier(srcs, dsts).run()


def _copy(src: Path, dst: Path) -> None:
    """
    Copies file or directory from source to destination.

    Directories are copied recursively.
    """
    logging.debug("Copying %s to %s", src, dst)
    if src.is_file():
        shutil.copy(src, dst)
    else:
        if dst.is_dir():
            shutil.rmtree(dst)
        shutil.copytree(src, dst)
