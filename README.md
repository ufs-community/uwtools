# workflow-tools
Unified Workflow tools for use with applications with UFS and beyond

## Installation
Simple installation instructions
```sh
$> git clone https://github.com/ufs-community/workflow-tools
$> cd workflow-tools
$> pip install .
```

## Documentation
The inline-documentation docstring standard (using the [NumPy](https://numpydoc.readthedocs.io/en/latest/format.html#docstring-standard) convention) will be used to describe modules, funtions, classes and methods for inline code documentation.

Documentation is automatically generated through [Read the Docs](https://readthedocs.org/) when [develop](https://github.com/ufs-community/workflow-tools/tree/develop) is updated and available [here](https://unified-workflow.readthedocs.io/en/latest/).

## Running Tests
Standard tests
`python -m pytest`

With coverage
`python -m pytest --cov=src`

With coverage report in html
`python -m pytest --cov=src --cov-report html`