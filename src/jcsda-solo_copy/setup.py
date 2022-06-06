#
# SOLO
#
# setup.py - Python setuptools integration
#

import setuptools

setuptools.setup(
    name="solo",
    version="1.0.0",
    author="JCSDA",
    description="Useful tools for Python",
    url="https://github.com/jcsda/solo",
    package_dir = {"":"src"},
    packages = setuptools.find_packages(where="src"),
    classifiers=[
        "Development Status :: 1 - Planning",
        "Environment :: Console",
        "Intended Audience :: Science/Research/Developers",
        "Programming Language :: Python :: 3 :: Only",
        "License :: OSI Approved :: Apache Software License",
        "Natural Language :: English",
        "Operating System :: OS Independent"],
    python_requires='>=3.6',
    install_requires=[
        "pyyaml >=5.3.1",
    ]
)
