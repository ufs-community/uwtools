"""
Basic setuptools configuration
"""

import json
import os

from setuptools import find_packages, setup  # type: ignore

with open(os.path.join(os.environ["RECIPE_DIR"], "meta.json"), "r", encoding="utf-8") as f:
    meta = json.load(f)

name_conda = meta["name"]
name_py = name_conda.replace("-", "_")

setup(
    entry_points={
        "console_scripts": [
            "atparse-to-jinja2 = %s.cli.atparse_to_jinja2:main" % name_py,
            "run-forecast = %s.cli.run_forecast:main" % name_py,
            "set-config = %s.cli.set_config:main" % name_py,
            "template = %s.cli.templater:main" % name_py,
        ]
    },
    name=name_conda,
    packages=find_packages(include=[name_py, "%s.*" % name_py]),
    version=meta["version"],
)
