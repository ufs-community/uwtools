from importlib import import_module
from os.path import abspath, dirname, join
from sys import path


def run(module: str) -> None:
    path.insert(0, abspath("%s/../src" % join(dirname(__file__))))
    import_module(f"uwtools.cli.{module}").main()
