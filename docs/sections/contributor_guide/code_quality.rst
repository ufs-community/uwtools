Code Quality
============

.. include:: links.rst

In an active development shell, the following ``make`` targets are available and act on all ``.py`` files under ``src/``:

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

Note that ``make format`` is never run automatically, to avoid reformatting under-development code in a way that might surprise the developer. A useful development idiom is to periodically run ``make format && make test`` to perform a full code-quality sweep through the code. An additional check is run by the CI for unformatted code, ``make format`` must be run, and then changes from ``make format`` must be committed before CI will pass.

The ``make test`` command is also automatically executed when ``conda`` builds a ``uwtools`` package, so it is important to periodically run these tests during development and, crucially, before merging changes, to ensure that the tests will pass when CI builds the ``workflow-tools`` code.


The order of the targets above is intentional, and possibly useful:

   * ``make format`` will complain about certain kinds of syntax errors that would cause all the remaining code-quality tools to fail (and may change line numbers reported by other tools, if it ran after them).
   * ``make lint`` provides a good first check for obvious errors and anti-patterns in the code.
   * ``make typecheck`` offers a more nuanced look at interfaces between functions, methods, etc. and may spot issues that would cause ``make unittest`` to fail.
