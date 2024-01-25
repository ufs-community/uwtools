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
project = "Unified Workflow Tools"
release = _metadata["version"]
version = _metadata["version"]

extlinks = {
    "anaconda": ("https://www.anaconda.com/%s", "%s"),
    "anaconda-condev": ("https://anaconda.org/maddenp/condev/%s", "%s"),
    "black": ("https://black.readthedocs.io/en/stable/%s", "%s"),
    "cmeps": ("https://escomp.github.io/CMEPS/versions/master/html/esmflds.html#%s", "%s"),
    "conda": ("https://docs.conda.io/en/latest/%s", "%s"),
    "conda-forge": ("https://conda-forge.org/%s", "%s"),
    "condev": ("https://github.com/maddenp/condev/%s", "%s"),
    "coverage": ("https://coverage.readthedocs.io/en/7.3.4/%s", "%s"),
    "docformatter": ("https://docformatter.readthedocs.io/en/stable/%s", "%s"),
    "github-docs": ("https://docs.github.com/en/%s", "%s"),
    "isort": ("https://pycqa.github.io/isort/%s", "%s"),
    "jinja2": ("https://jinja.palletsprojects.com/%s", "%s"),
    "jq": ("https://jqlang.github.io/jq/manual/v1.7/%s", "%s"),
    "json-schema": ("https://json-schema.org/%s", "%s"),
    "miniconda": ("https://docs.conda.io/projects/miniconda/en/latest/%s", "%s"),
    "miniforge": ("https://github.com/conda-forge/miniforge/%s", "%s"),
    "miniforge3": ("https://github.com/conda-forge/miniforge/%s", "%s"),
    "mypy": ("https://mypy.readthedocs.io/en/stable/%s", "%s"),
    "pylint": ("https://pylint.readthedocs.io/en/v3.0.3/%s", "%s"),
    "pytest": ("https://docs.pytest.org/en/7.4.x/%s", "%s"),
    "rocoto": ("https://christopherwharrop.github.io/rocoto/%s", "%s"),
    "rst": ("https://www.sphinx-doc.org/en/master/usage/restructuredtext/%s", "%s"),
    "rtd": ("https://readthedocs.org/projects/uwtools/%s", "%s"),
    "ufs": ("https://ufscommunity.org/%s", "%s"),
    "ufs-weather-model": ("https://github.com/ufs-community/ufs-weather-model/%s", "%s"),
    "uwtools": ("https://github.com/ufs-community/uwtools/%s", "%s"),
    "weather-model-io": ("https://ufs-weather-model.readthedocs.io/en/latest/InputsOutputs.html#%s", "%s"),
}

def setup(app):
    app.add_css_file("custom.css")
