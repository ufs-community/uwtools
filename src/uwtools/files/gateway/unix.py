# pylint: disable=too-few-public-methods
"""
Unix based local file copying, threaded
"""

import logging
import os
import pathlib
import shutil
from queue import Empty, Queue
from threading import Thread
from typing import List

from uwtools.files.model import File

logging.getLogger(__name__)


def copy(source: List[File], destination: List[pathlib.Path]):  # pylint: disable=unused-variable
    """copies each item from source to corresponding item in destination"""
    Copier(source, destination).run()


class Copier:
    """represents a threaded file copier"""

    def __init__(self, source: List[File], destination: List[pathlib.Path]):
        self.source = list(source)
        self.destination = list(destination)
        self.queue: Queue = Queue()
        self.append(source, destination)

    def __iter__(self):
        try:
            yield self.queue.get_nowait()
        except Empty:
            return

    def append(self, source, destination):
        """append a task to the queue"""
        for src, dest in zip(list(source), list(destination)):
            self.queue.put((src, dest))

    def run(self):
        """runs all tasks in queue threaded"""

        threads = [
            Thread(target=_copy, args=(source.path, destination)) for (source, destination) in self
        ]

        for thread in threads:
            thread.start()

        # wait to complete
        for thread in threads:
            thread.join()


def _copy(source: pathlib.Path, destination: pathlib.Path):
    """copies file or directory from src to destination.

    Directories are copied recursively.
    """
    logging.debug("copying %s to %s", source, destination)
    if os.path.exists(destination) and os.path.isdir(destination):
        shutil.rmtree(destination)
        shutil.copytree(source, destination)
        return
    shutil.copy(source, destination)
