"""
Basic setuptools configuration.

See https://setuptools.pypa.io/en/latest/userguide/quickstart.html#basic-use for
information on this standard setuptools file.

In this codebase, it is used 1. By conda-build to install the uwtools files into
the package tree, and 2. By condev-shell (called by "make devshell") to perform
an "editable" install into the conda development environment, such that source
files in the clone are live-linked into the conda environment so that they can
be executed in a context where all build/run/test dependency packages are
available.
"""

import json
import os

from setuptools import find_packages, setup  # type: ignore

recipe = os.environ.get("RECIPE_DIR", "../recipe")
with open(os.path.join(recipe, "meta.json"), "r", encoding="utf-8") as f:
    meta = json.load(f)

name_conda = meta["name"]
name_py = name_conda.replace("-", "_")

kwargs = {
    "entry_points": {"console_scripts": ["uw = %s.cli:main" % name_py]},
    "name": name_conda,
    "packages": find_packages(exclude=["%s.tests" % name_py], include=[name_py, "%s.*" % name_py]),
    "version": meta["version"],
}

if not os.environ.get("CONDA_PREFIX"):
    kwargs["install_requires"] = [x.replace(" =", "==") for x in meta["packages"]["run"]]

setup(**kwargs)
