# pylint: disable=too-few-public-methods, unused-variable

import pathlib
from queue import Empty, Queue
import shutil
from threading import Thread
from typing import List

from uwtools.files.model import File, Unix


def copy(source: List[File], destination: List[pathlib.Path]):
    """copies each item from source to corresponding item in destination"""
    Copier(source, destination).run()


class Copier:
    """represents a threaded file copier"""

    def __init__(self, source: List[File], destination: List[pathlib.Path]):
        self.source = list(source)
        self.destination = list(destination)
        self.queue = Queue()
        self.append(source, destination)

    def __iter__(self):
        try:
            yield from self.queue.get_nowait()
        except Empty:
            return

    def append(self, source, destination):
        for (src, dest) in zip(list(source), list(destination)):
            self.queue.put((src, dest))

    def run(self):
        for x in self:
            print(x)
        threads = [
            Thread(target=shutil.copy, args=(source.path, destination.path))
            for (source, destination) in self
        ]

        # start the threads
        for thread in threads:
            thread.start()

        # wait for the threads to complete
        for thread in threads:
            thread.join()


def _copy(source: pathlib.Path, destination: pathlib.Path):
    """copies file or directory from src to destination.

    Directories are coppied recursively.
    """
    logging.debug("copying %s to %s", source, destination)
    if os.path.exists(destination) and os.path.isdir(destination):
        shutil.rmtree(destination)
        shutil.copytree(source, destination)
        return
    shutil.copy(source, destination)
