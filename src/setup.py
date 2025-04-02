"""
Basic setuptools configuration.

See https://setuptools.pypa.io/en/latest/userguide/quickstart.html#basic-use for information on
this standard setuptools file.

Here it is used 1. By conda-build to install the uwtools files into the package tree; 2. By "make
devshell" to perform an "editable" install into the conda development environment, such that source
files in the clone are live-linked into the conda environment so that they can be executed in a
context where all build/run/test dependency packages are available; and 3. By pip users to install
the local package along with its dependencies from PyPI.
"""

import json
import os
import re
from pathlib import Path

from setuptools import find_packages, setup

# Collect package metadata.

recipe = Path(os.environ.get("RECIPE_DIR", "../recipe"))
metasrc = recipe / "meta.json"
with metasrc.open() as f:
    meta = json.load(f)
name_conda = meta["name"]
name_py = name_conda.replace("-", "_")

# Define basic setup configuration.

kwargs = {
    "entry_points": {"console_scripts": ["uw = %s.cli:main" % name_py]},
    "include_package_data": True,
    "name": name_conda,
    "packages": find_packages(exclude=["%s.tests" % name_py], include=[name_py, "%s.*" % name_py]),
    "version": meta["version"],
}

# Define dependency packages for non-devshell installs.

if not os.environ.get("CONDEV_SHELL"):
    kwargs["install_requires"] = [
        pkg.replace(" =", "==")
        for pkg in meta["packages"]["run"]
        if not re.match(r"^python .*$", pkg)
    ]

# Install.

setup(**kwargs)
