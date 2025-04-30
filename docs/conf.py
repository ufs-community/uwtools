# See https://www.sphinx-doc.org/en/master/usage/configuration.html

import datetime as dt
import json
import os
import sys

sys.path.insert(0, os.path.abspath("../src"))

with open("../recipe/meta.json", "r", encoding="utf-8") as f:
    _metadata = json.loads(f.read())

autoclass_content = "both"
autodoc_mock_imports = ["f90nml", "iotaa", "jsonschema", "lxml", "referencing"]
autodoc_typehints = "description"
copyright = str(dt.datetime.now().year)
exclude_patterns = ["**/shared/*.rst"]
extensions = ["sphinx.ext.autodoc", "sphinx.ext.extlinks", "sphinx.ext.intersphinx"]
extlinks_detect_hardcoded_links = True
html_logo = os.path.join("static", "ufs.png")
html_static_path = ["static"]
html_theme = "sphinx_rtd_theme"
intersphinx_mapping = {"python": ("https://docs.python.org/3", None)}
nitpick_ignore = [
    ("py:class", "Path"),
    ("py:class", "f90nml.Namelist"),
    ("py:class", "iotaa.Asset"),
    ("py:class", "iotaa.Node"),
]
numfig = True
numfig_format = {"figure": "Figure %s"}
project = "Unified Workflow Tools"
release = _metadata["version"]
user_agent = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36"
version = _metadata["version"]

extlinks = {
    "anaconda": ("https://www.anaconda.com/%s", "%s"),
    "anaconda-condev": ("https://anaconda.org/maddenp/condev/%s", "%s"),
    "black": ("https://black.readthedocs.io/en/stable/%s", "%s"),
    "cdeps": ("https://escomp.github.io/CDEPS/versions/master/html/%s", "%s"),
    "cmeps": ("https://escomp.github.io/CMEPS/versions/master/html/esmflds.html#%s", "%s"),
    "conda": ("https://docs.conda.io/en/latest/%s", "%s"),
    "conda-forge": ("https://conda-forge.org/%s", "%s"),
    "condev": ("https://github.com/maddenp/condev/%s", "%s"),
    "coverage": ("https://coverage.readthedocs.io/en/7.3.4/%s", "%s"),
    "docformatter": ("https://docformatter.readthedocs.io/en/stable/%s", "%s"),
    "fre-nctools": ("https://github.com/NOAA-GFDL/FRE-NCtools/blob/main/src/make-hgrid/%s", "%s"),
    "github-docs": ("https://docs.github.com/en/%s", "%s"),
    "iotaa-readme": ("https://github.com/maddenp/iotaa/blob/main/README.md#%s", "%s"),
    "isort": ("https://pycqa.github.io/isort/%s", "%s"),
    "jinja2": ("https://jinja.palletsprojects.com/%s", "%s"),
    "jq": ("https://jqlang.github.io/jq/manual/v1.7/%s", "%s"),
    "json-schema": ("https://json-schema.org/%s", "%s"),
    "miniconda": ("https://docs.conda.io/projects/miniconda/en/latest/%s", "%s"),
    "miniforge": ("https://github.com/conda-forge/miniforge/%s", "%s"),
    "mpas": ("https://www.mmm.ucar.edu/models/mpas/%s", "%s"),
    "mypy": ("https://mypy.readthedocs.io/en/stable/%s", "%s"),
    "noaa": ("https://www.noaa.gov/%s", "%s"),
    "pylint": ("https://pylint.readthedocs.io/en/stable/%s", "%s"),
    "pytest": ("https://docs.pytest.org/en/7.4.x/%s", "%s"),
    "python": ("https://docs.python.org/3/library/%s", "%s"),
    "rocoto": ("https://christopherwharrop.github.io/rocoto/%s", "%s"),
    "rst": ("https://www.sphinx-doc.org/en/master/usage/restructuredtext/%s", "%s"),
    "rtd": ("https://readthedocs.org/projects/uwtools/%s", "%s"),
    "schism": ("https://schism-dev.github.io/schism/master/%s", "%s"),
    "sfc-climo-gen": ("https://ufs-community.github.io/UFS_UTILS/sfc_climo_gen/%s", "%s"),
    "ufs": ("https://ufs.epic.noaa.gov/%s", "%s"),
    "ufs-utils": ("https://noaa-emcufs-utils.readthedocs.io/en/latest/ufs_utils.html#%s", "%s"),
    "ufs-weather-model": ("https://github.com/ufs-community/ufs-weather-model/%s", "%s"),
    "uwtools": ("https://github.com/ufs-community/uwtools/%s", "%s"),
    "weather-model-io": ("https://ufs-weather-model.readthedocs.io/en/latest/InputsOutputs.html#%s", "%s"),
    "ww3": ("https://polar.ncep.noaa.gov/waves/wavewatch/%s", "%s"),
}

def setup(app):
    app.add_css_file("custom.css")
