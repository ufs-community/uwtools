Code Quality
============

In an active development shell, the following ``make`` targets are available and act on all ``.py`` files under ``src/``:

.. list-table::
   :widths: 15 85
   :header-rows: 1

   * - Command
     - Description
   * - ``make format``
     - Formats code and imports with :ruff:`ruff<>`, docstrings with :docformatter:`docformatter<>`, and ``.json*`` documents with :jq:`jq<>`
   * - ``make lint``
     - Lints code with :ruff:`ruff<>`
   * - ``make typecheck``
     - Typechecks code with :mypy:`mypy<>`
   * - ``make unittest``
     - Runs unit tests and reports coverage with :pytest:`pytest<>` and :coverage:`coverage<>`
   * - ``make test``
     - Equivalent to ``make lint && make typecheck && make unittest``, plus checks defined CLI scripts.

Configuration for these tools is provided by the file ``src/pyproject.toml``.

The order of the targets above is intentional:

   * ``make format`` will complain about certain kinds of syntax errors that would cause all the remaining code-quality tools to fail (and that could change line numbers reported by other tools, if it ran after them).
   * ``make lint`` provides a good first check for obvious errors and anti-patterns in the code.
   * ``make typecheck`` offers a more nuanced look at interfaces between functions, methods, etc. and may spot issues missed by the linter.
   * ``make unittest`` provides higher-level semantic-correctness checks once code syntax and typing is deemed correct.

All the above tests are executed by the CI system when code is merged to specific git branches and when a conda package is built for release. To ensure that these processes succeed, be sure to run all the tests in a development shell before opening a pull request, and throughout the PR's lifecycle as subsequent changes are made. CI will reject unformatted code, so also run ``make format`` and commit any changes it makes. A useful development idiom is to periodically run ``make format && make test`` to perform a full code-quality sweep through the code.

The ``uwtools`` repository has standardized 100% unit-test coverage, enforced by ``make unittest`` and its configuration in ``pyproject.toml``. Please help maintain this high standard.
