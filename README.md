[![Documentation](https://github.com/ufs-community/workflow-tools/actions/workflows/docs.yaml/badge.svg)](https://github.com/ufs-community/workflow-tools/actions/workflows/docs.yaml)

# workflow-tools

Unified Workflow tools for use with applications with UFS and beyond

## Installation

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

## Development

### Creating a development shell

To create an interactive development `bash` shell:

1. Download, install, and activate the latest [Miniforge3](https://github.com/conda-forge/miniforge#download) for your system. If an existing conda (Miniforge, Miniconda, Anaconda, etc.) installation is available and writable, you may activate that and skip the first 5 recipe steps below.
2. Install the [condev](https://github.com/maddenp/condev) package into the base environment.
3. In a clone of the [workflow-tools repository](https://github.com/ufs-community/workflow-tools), create the development shell.

This recipe uses the `aarch64` (64-bit ARM) Miniforge for Linux, and installs into `$HOME/conda`. Adjust as necessary for your target system.

``` sh
wget https://github.com/conda-forge/miniforge/releases/latest/download/Miniforge3-Linux-aarch64.sh
bash Miniforge3-Linux-aarch64.sh -bfp ~/conda
rm Miniforge3-Linux-aarch64.sh
source ~/conda/etc/profile.d/conda.sh
conda activate
conda install -y -c maddenp condev
cd /to/your/workflow-tools/clone
make devshell
```

If the above is successful, you will be in a `workflow-tools` development shell. See below for usage information. You may exit the shell with `exit` or `ctrl-d`.

Future `make devshell` invocations will be almost instantaneous, as the underlying virtual environment will already exist. In general, all source code changes will be immediately live in the development shell, subject to execution, test, etc. But some changes -- especially to the contents of the `recipe/` directory, or to the `src/setup.py` module -- may require recreation of the development shell. If you know this is needed, or when in doubt: Exit the development shell, run `conda env remove -n DEV-uwtools` to remove the old environment, then run `make devshell` to recreate it.

If your development shell misses any functionality you're used to in your main shell, you can create a `~/.condevrc` file, which will be sourced by `make devshell`. When in doubt, you might

``` sh
cat <<EOF >~/.condevrc
source ~/.bashrc
EOF
```

### Using a development shell

In an active development shell, the following `make` targets are available and act on all `.py` files under `src/`:

| Command          | Description                                                                                   |
| ---------------- | --------------------------------------------------------------------------------------------- |
| `make format`    | Format with `black` and `isort`                                                               |
| `make lint`      | Lint with `pylint`                                                                            |
| `make typecheck` | Typecheck with `mypy`                                                                         |
| `make unittest`  | Run unit tests and report coverage with `pytest` and `coverage`                               |
| `make test`      | Equivalent to `make lint && make typecheck && make unittest`, plus checks defined CLI scripts |

Note that `make format` is never run automatically, to avoid reformatting under-development code in a way that might surprise the developer. A useful development idiom is to periodically run `make format && make test` to perform a full code-quality sweep through the code.

The order of the targets above is intentionally, and possibly useful: `make format` will complain about certain kinds of syntax errors that would cause all the remaining code-quality tools to fail (and may change line numbers reported by other tools, if it ran after them); `make lint` provides a good first check for obvious errors and anti-patterns in the code; `make typecheck` offers a more nuanced look at interfaces between functions, methods, etc. and may spot issues that would cause `make unittest` to fail.

The `make test` command is also automatically executed when `conda` builds a `uwtools` package, so it is important to periodically run these tests during development and, crucially, before merging changes, to ensure that the tests will pass when CI builds the `workflow-tools` code.

In addition to the `make devshell` command, two other `make` targets are available for use *outside* a development shell, i.e. from the base conda environment (requires presence of the `condev` package):

| Command          | Description                                                |
| ---------------- | ---------------------------------------------------------- |
| `make package`   | Builds a `uwtools` conda package                           |
| `make env`       | Creates a conda environment based on the `uwtools` code    |

These targets work from the code in its current state in the clone. `make env` calls `make package` automatically to create a local package, then builds an environment based on the package.

### Building condev locally

As an alternative to installing a prebuilt package from [anaconda.org](https://anaconda.org/), the `condev` package can be built locally, then installed into the local conda installation. Ensure that `conda-build` and `conda-verify` are installed in the base environment.

``` sh
# Activate your conda
git clone https://github.com/maddenp/condev.git
make -C condev package
conda install -y -c local condev
```

### Files derived from condev

The following files in this repo are derived from their counterparts in the [condev demo](https://github.com/maddenp/condev/tree/main/demo):

``` sh
├── Makefile
├── recipe
│   ├── build.sh
│   ├── channels
│   ├── conda_build_config.yaml
│   ├── .gitignore
│   ├── meta.yaml
│   └── run_test.sh
├── src
│   ├── pyproject.toml
│   ├── setup.py
```

Behaviors described in previous sections may rely on these files continuing to follow `condev` conventions.

## Documentation

The inline-documentation docstring standard (using the [NumPy](https://numpydoc.readthedocs.io/en/latest/format.html#docstring-standard) convention) will be used to describe modules, funtions, classes and methods for inline code documentation.

Documentation is automatically generated through [Read the Docs](https://readthedocs.org/) when [develop](https://github.com/ufs-community/workflow-tools/tree/develop) is updated and available [here](https://unified-workflow.readthedocs.io/en/latest/).

[Developer Status](https://github.com/orgs/ufs-community/projects/1)

[UW Tools Github Pages Site](https://ufs-community.github.io/workflow-tools/)

