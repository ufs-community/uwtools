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
extensions = ["sphinx.ext.autodoc", "sphinx.ext.extlinks", "sphinx.ext.intersphinx"]
extlinks_detect_hardcoded_links = True
html_logo = os.path.join("static", "ufs.png")
html_static_path = ["static"]
html_theme = "sphinx_rtd_theme"
intersphinx_mapping = {"python": ("https://docs.python.org/3", None)}
nitpick_ignore_regex = [("py:class", r"^uwtools\..*")]
numfig = True
numfig_format = {"figure": "Figure %s"}
project = "Unified Workflow"
release = _metadata["version"]
version = _metadata["version"]

extlinks = {
    "anaconda": ("https://anaconda.org/%s", "%s"),
    "anaconda-condev": ("https://anaconda.org/maddenp/condev/%s", "%s"),
    "black": ("https://black.readthedocs.io/en/stable/%s", "%s"),
    "conda": ("https://docs.conda.io/en/latest/%s", "%s"),
    "conda-forge": ("https://conda-forge.org/%s", "%s"),
    "condev": ("https://github.com/maddenp/condev/%s", "%s"),
    "coverage": ("https://coverage.readthedocs.io/en/7.2.7/%s", "%s"),
    "docformatter": ("https://docformatter.readthedocs.io/en/stable/%s", "%s"),
    "isort": ("https://pycqa.github.io/isort/%s", "%s"),
    "jq": ("https://jqlang.github.io/jq/manual/v1.6/%s", "%s"),
    "json-schema": ("https://json-schema.org/%s", "%s"),
    "miniconda": ("https://docs.conda.io/projects/miniconda/en/latest/%s", "%s"),
    "miniforge": ("https://github.com/conda-forge/miniforge/%s", "%s"),
    "miniforge3": ("https://github.com/conda-forge/miniforge/%s", "%s"),
    "mypy": ("https://mypy.readthedocs.io/en/stable/%s", "%s"),
    "pylint": ("https://pylint.readthedocs.io/en/stable/%s", "%s"),
    "pytest": ("https://docs.pytest.org/en/stable/%s", "%s"),
    "rocoto": ("https://christopherwharrop.github.io/rocoto/%s", "%s"),
    "semver": ("https://semver.org/%s", "%s"),
    "uwtools": ("https://github.com/ufs-community/workflow-tools/%s", "%s"),
}

def setup(app):
    app.add_css_file("custom.css")
