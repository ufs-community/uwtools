Developer Setup
===============

.. include:: links.rst

Creating a ``bash`` development shell
-------------------------------------

.. include:: ../miniforge3_instructions.rst

2. Install the `condev`_ package into the base environment.

   .. code:: sh

     conda install -y -c maddenp condev

3. In a clone of the `workflow-tools repository`_, create the development shell.

   .. code:: sh

     cd /to/your/workflow-tools/clone
     make devshell

If the above is successful, you will be in a ``workflow-tools`` development shell. See below for usage information. You may exit the shell with ``exit`` or ``ctrl-d``.

Future ``make devshell`` invocations will be almost instantaneous, as the underlying virtual environment will already exist. In general, all source code changes will be immediately live in the development shell, subject to execution, test, etc. But some changes – especially to the contents of the ``recipe/`` directory, or to the ``src/setup.py`` module – may require recreation of the development shell. If you know this is needed, or when in doubt:

    1. Exit the development shell, run ``conda env remove -n DEV-uwtools`` to remove the old environment.
    2. Run ``make devshell`` to recreate it.

If your development shell misses any functionality you’re used to in your main (``bash``) shell, you can create a ``~/.condevrc`` file, which will be sourced by ``make devshell``. When in doubt, you might:

   .. code::

     cat <<EOF >~/.condevrc
     source ~/.bashrc
     EOF

Using a ``bash`` development shell
----------------------------------

In an active development shell, the following ``make`` targets are available and act on all ``.py`` files under ``src/``:

.. include:: code_quality_tools_table.rst

Note that ``make format`` is never run automatically, to avoid reformatting under-development code in a way that might surprise the developer. A useful development idiom is to periodically run ``make format && make test`` to perform a full code-quality sweep through the code. An additional check is run by the CI for unformatted code, ``make format`` must be run, and then changes from ``make format`` must be committed before CI will pass.

The ``make test`` command is also automatically executed when ``conda`` builds a ``uwtools`` package, so it is important to periodically run these tests during development and, crucially, before merging changes, to ensure that the tests will pass when CI builds the ``workflow-tools`` code.


The order of the targets above is intentional, and possibly useful:

   * ``make format`` will complain about certain kinds of syntax errors that would cause all the remaining code-quality tools to fail (and may change line numbers reported by other tools, if it ran after them).
   * ``make lint`` provides a good first check for obvious errors and anti-patterns in the code.
   * ``make typecheck`` offers a more nuanced look at interfaces between functions, methods, etc. and may spot issues that would cause ``make unittest`` to fail.


In addition to the ``make devshell`` command, other ``make`` targets are available for use *outside* a development shell, i.e. from the base conda environment (requires presence of the ``condev`` package):


.. list-table::
   :widths: 15 85
   :header-rows: 1

   * - Command
     - Description
   * - ``make env``
     - Creates a conda environment based on the ``uwtools`` code
   * - ``make meta``
     - Update ``recipe/meta.json`` from ``recipe/meta.yaml``
   * - ``make package``
     - Builds a ``uwtools`` conda package

These targets work from the code in its current state in the clone. ``make env`` calls ``make package`` automatically to create a local package, then builds an environment based on the package.

Building condev locally
-----------------------

As an alternative to installing `a prebuilt package from anaconda <https://anaconda.org/maddenp/condev>`_, the ``condev`` package can be built locally, then installed into the local conda installation. Ensure that ``conda-build`` and ``conda-verify`` are installed in the base environment:

   .. code:: sh

     # Activate your conda
     git clone https://github.com/maddenp/condev.git
     make -C condev package
     conda install -y -c local condev

Files derived from condev
-------------------------

The following files in this repo are derived from their counterparts in the `condev demo`_ and are used by ``condev`` code when running certain make commands

   .. code:: sh

     ├── Makefile
     ├── recipe
     │   ├── build.sh
     │   ├── channels
     │   ├── meta.json
     │   ├── meta.yaml
     │   └── run_test.sh
     ├── src
     │   ├── pyproject.toml
     │   ├── setup.py
