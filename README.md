[![Run tests](https://github.com/ufs-community/workflow-tools/actions/workflows/tests.yaml/badge.svg)](https://github.com/ufs-community/workflow-tools/actions/workflows/tests.yaml)
[![Documentation](https://github.com/ufs-community/workflow-tools/actions/workflows/docs.yaml/badge.svg)](https://github.com/ufs-community/workflow-tools/actions/workflows/docs.yaml)
[![CodeFactor](https://www.codefactor.io/repository/github/ufs-community/workflow-tools/badge)](https://www.codefactor.io/repository/github/ufs-community/workflow-tools)
# workflow-tools

Unified Workflow tools for use with applications with UFS and beyond

## Installation
Simple installation instructions with a conda environment
Substitute <workflow-tools location> with your install directory
```sh
$> git clone https://github.com/ufs-community/workflow-tools
$> conda env create -f environment.yml
$> conda activate workflow_tools
$> cd workflow-tools
$> export PYTHONPATH=<workflow-tools location>/src:$PYTHONPATH
$> pip install -r requirements.txt
```

## Documentation
The inline-documentation docstring standard (using the [NumPy](https://numpydoc.readthedocs.io/en/latest/format.html#docstring-standard) convention) will be used to describe modules, funtions, classes and methods for inline code documentation.

Documentation is automatically generated through [Read the Docs](https://readthedocs.org/) when [develop](https://github.com/ufs-community/workflow-tools/tree/develop) is updated and available [here](https://unified-workflow.readthedocs.io/en/latest/).

[Developer Status](https://github.com/orgs/ufs-community/projects/1)

[UW Tools Github Pages Site](https://ufs-community.github.io/workflow-tools/)