#!/usr/bin/env python3

from importlib import import_module
from os.path import abspath, dirname, join
from sys import path


path.insert(0, abspath("%s/../src" % join(dirname(__file__))))
import_module("uwtools.cli.run_forecast").main()
