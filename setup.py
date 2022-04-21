
#!/usr/bin/env python
# -*- coding: utf-8 -*-

# pylint: disable=missing-module-docstring

import os
import sys
import codecs
import subprocess

from setuptools import setup

here = os.path.abspath(os.path.dirname(__file__))

with codecs.open(os.path.join(here, "README.md"), encoding="utf-8") as f:
    long_description = "\n" + f.read()


if sys.argv[-1] == "publish":
    subprocess.call(f"{sys.executable} setup.py sdist bdist_wheel upload", shell=False)
    sys.exit()

required = [""]

setup(
    name="owtools",
    version="0.0.0",
    description="Unified workflow tools",
    long_description=long_description,
    long_description_content_type="text/x-rst",
    url="",
    py_modules=[""],
    install_requires=required,
    tests_require=["pytest"],
    license="MIT",
    classifiers=[
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
    ],
    extras_require={  # Optional
        "dev": [
            "check-manifest",
            "black",
            "pylint",
            "pytest",
            "pytest-cov",
            "pytest-xdist",
            "tox",
            "bump2version",
        ],
        "test": ["pytest", "pytest-cov", "pytest-forked", "pytest-xdist", "tox"],
    },
)
