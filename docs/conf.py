# See https://www.sphinx-doc.org/en/master/usage/configuration.html

import datetime as dt
import json
import os
import sys

sys.path.insert(0, os.path.abspath("../src"))

with open("../recipe/meta.json", "r", encoding="utf-8") as f:
    _metadata = json.loads(f.read())

autodoc_mock_imports = ["f90nml", "jsonschema", "lxml"]
copyright = str(dt.datetime.now().year)
extensions = ["sphinx.ext.autodoc", "sphinx.ext.intersphinx"]
html_logo = os.path.join("static", "ufs.png")
html_theme = "sphinx_rtd_theme"
intersphinx_mapping = {"python": ("https://docs.python.org/3", None)}
nitpick_ignore_regex = [("py:class", r"^uwtools\..*")]
numfig = True
numfig_format = {"figure": "Figure %s"}
project = "Unified Workflow"
release = _metadata["version"]
version = _metadata["version"]
