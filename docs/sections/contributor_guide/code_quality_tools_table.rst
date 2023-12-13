.. include:: links.rst

.. list-table::
   :widths: 15 85
   :header-rows: 1

   * - Command
     - Description
   * - ``make format``
     - Formats code with `black`_, imports with `isort`_, docstrings with `docformatter`_, and ``.jsonschema`` documents with `jq`_
   * - ``make lint``
     - Lints code with `pylint`_
   * - ``make typecheck``
     - Typechecks code with `mypy`_
   * - ``make unittest``
     - Runs unit tests and reports coverage with `pytest`_ and `coverage`_
   * - ``make test``
     - Equivalent to ``make lint && make typecheck && make unittest``, plus checks defined CLI scripts.
