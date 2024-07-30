Developer Setup
===============

Creating a ``bash`` Development Shell
-------------------------------------

If an existing conda (:miniforge:`Miniforge<>`, :miniconda:`Miniconda<>`, :anaconda:`Anaconda<>`, etc.) installation is available and writable, step 1 may be skipped.

.. include:: /shared/miniforge_instructions.rst

#. Install the :anaconda-condev:`condev package<>` into the ``base`` environment.

   .. code-block:: text

      conda install -y -c maddenp -c conda-forge --override-channels condev

#. In a clone of the :uwtools:`uwtools repository<>`, create the development shell.

   .. code-block:: text

      cd /to/your/uwtools/clone
      make devshell

If the above is successful, you will be in a ``uwtools`` development shell. See below for usage information. You may exit the shell with ``exit`` or ``ctrl-d``.

Future ``make devshell`` invocations will be almost instantaneous, as the underlying virtual environment will already exist. In general, all source code changes will be immediately live in the development shell, subject to execution, test, etc. But some changes --- especially to the contents of the ``recipe/`` directory or to the ``src/setup.py`` module --- may require recreation of the development shell. If you know this is needed, or when in doubt:

  #. Exit the development shell.
  #. Run ``make clean-devenv`` (or ``conda env remove -y -n DEV-uwtools``) to remove the old environment.
  #. Run ``make devshell`` to recreate it.

If your development shell misses any functionality you’re used to in your main (``bash``) shell, you can create a ``~/.condevrc`` file, which will be sourced by ``make devshell``, and add desired environment-setup commands to it.

If using an IDE such as VS Code, ensure that the correct Python interpreter belonging to the conda environment providing uwtools is selected. In VS Code, this can be changed by using the Command Palette and searching "Python: Select Interpreter".

Using a ``bash`` Development Shell
----------------------------------

A development shell makes available several code-formatting and quality checkers, which should be periodically run during the development process. See :doc:`Code Quality <code_quality>` for full details.

In addition to the ``make devshell`` command, other ``make`` targets are available for use *outside* a development shell, i.e., from the ``base`` conda environment (requires presence of the ``condev`` package):

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

Building ``condev`` Locally
---------------------------

As an alternative to installing the :anaconda-condev:`pre-built package<>`, the ``condev`` package can be built locally, then installed into the local conda:

.. code-block:: text

   # Activate your conda. Optionally, activate a non-'base' environment.
   conda install -y conda-build conda-verify
   git clone https://github.com/maddenp/condev.git
   make -C condev package
   conda install -y -c $CONDA_PREFIX/conda-bld -c conda-forge --override-channels condev

Files Derived from ``condev``
-----------------------------

The following files in this repository are derived from their counterparts in the :condev:`condev demo<tree/main/demo>` and are used by ``condev`` code when running certain ``make`` commands

.. code-block:: text

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
