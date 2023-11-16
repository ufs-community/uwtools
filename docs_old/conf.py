# See https://www.sphinx-doc.org/en/master/usage/configuration.html

import datetime as dt
import json
import os

with open("../recipe/meta.json", "r", encoding="utf-8") as f:
    _metadata = json.loads(f.read())

copyright = str(dt.datetime.now().year)
html_logo = os.path.join("static", "ufs.png")
html_theme = "sphinx_rtd_theme"
numfig = True
numfig_format = {"figure": "Figure %s"}
project = "Unified Workflow"
release = _metadata["version"]
version = _metadata["version"]
