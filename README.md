[![docs](https://readthedocs.org/projects/unified-workflow/badge/?version=latest)](https://readthedocs.org/projects/unified-workflow/builds/)

# workflow-tools

Unified Workflow tools for use with UFS applications and beyond

## Documentation

Comprehensive documentation is available [here](https://unified-workflow.readthedocs.io/en/latest/).

## User Installation

- If you are a Developer, skip the User Installation and continue on to the Development section

The recommended installation mechanism uses the Python package and virtual-environment manager [conda](https://docs.conda.io/en/latest/). Specifically, these instructions detail the use of the minimal [Miniforge](https://github.com/conda-forge/miniforge) variant of [Miniconda](https://docs.conda.io/en/latest/miniconda.html), built to use, by default, packages from the [conda-forge](https://conda-forge.org/) project. Users of the original Miniconda (or the [Anaconda](https://anaconda.org/) distribution) may need to add the flags `-c conda-forge --override-channels` to `conda build`, `conda create`, and `conda install` commands to specify the use of conda-forge packages.

### Using a fresh Miniforge installation

1. Download, install, and activate the latest [Miniforge3](https://github.com/conda-forge/miniforge#download) for your system. If an existing conda (Miniforge, Miniconda, Anaconda, etc.) installation is available and writable, you may activate that and skip the first 5 recipe steps below.
2. Install the `conda-build` and `conda-verify` packages into the base environment. If `conda-build` and `conda-verify` are already installed in the your installation's base environment, you may skip this step.
3. In a clone of the [workflow-tools repository](https://github.com/ufs-community/workflow-tools), build and install the `uwtools` package.
4. Activate the `uwtools` environment.

This recipe uses the `aarch64` (64-bit ARM) Miniforge for Linux, and installs into `$HOME/conda`. Adjust as necessary for your target system.

``` sh
wget https://github.com/conda-forge/miniforge/releases/latest/download/Miniforge3-Linux-aarch64.sh
bash Miniforge3-Linux-aarch64.sh -bfp ~/conda
rm Miniforge3-Linux-aarch64.sh
source ~/conda/etc/profile.d/conda.sh
conda activate
conda install -y conda-build conda-verify
cd /to/your/workflow-tools/clone
conda build recipe
conda create -y -n uwtools -c local uwtools
conda activate uwtools
```

In future shells, you can activate and use this environment with

``` sh
source ~/conda/etc/profile.d/conda.sh
conda activate uwtools
```

Note that the `uwtools` package's actual name will contain version and build information, e.g. `uwtools-0.1.0-py_0`. The `conda create` command will find and use the most recent [semver](https://semver.org/)-compliant package name given the base name `uwtools`. It could also be explicitly specified as `uwtools=0.1.0=py_0`.
