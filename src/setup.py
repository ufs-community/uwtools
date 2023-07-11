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

setup(
    entry_points={
        "console_scripts": [
            "atparse-to-jinja2 = %s.cli.atparse_to_jinja2:main" % name_py,
            "experiment-manager = %s.cli.experiment_manager:main" % name_py,
            "run-forecast = %s.cli.run_forecast:main" % name_py,
            "set-config = %s.cli.set_config:main" % name_py,
            "template = %s.cli.templater:main" % name_py,
            "validate-config = %s.cli.validate_config:main" % name_py,
        ]
    },
    name=name_conda,
    packages=find_packages(
        exclude=["%s.tests" % name_py],
        include=[name_py, "%s.*" % name_py],
    ),
    version=meta["version"],
)
