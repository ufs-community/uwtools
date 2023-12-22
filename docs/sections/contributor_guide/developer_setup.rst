Developer Setup
===============

.. include:: links.rst

Creating a ``bash`` development shell
-------------------------------------

.. include:: ../../resources/miniforge3_instructions.rst

2. Install the `condev`_ package into the base environment.

  .. code:: sh

    conda install -y -c maddenp condev

3. In a clone of the `workflow-tools repository`_, create the development shell.

  .. code:: sh

    cd /to/your/workflow-tools/clone
    make devshell

If the above is successful, you will be in a ``workflow-tools`` development shell. See below for usage information. You may exit the shell with ``exit`` or ``ctrl-d``.

Future ``make devshell`` invocations will be almost instantaneous, as the underlying virtual environment will already exist. In general, all source code changes will be immediately live in the development shell, subject to execution, test, etc. But some changes – especially to the contents of the ``recipe/`` directory, or to the ``src/setup.py`` module – may require recreation of the development shell. If you know this is needed, or when in doubt:

  #. Exit the development shell.
  #. Run ``make clean-devenv`` (or ``conda env remove -n DEV-uwtools``) to remove the old environment.
  #. Run ``make devshell`` to recreate it.

If your development shell misses any functionality you’re used to in your main (``bash``) shell, you can create a ``~/.condevrc`` file, which will be sourced by ``make devshell``. When in doubt, you might:

.. code::

  cat <<EOF >~/.condevrc
  source ~/.bashrc
  EOF

Using a ``bash`` development shell
----------------------------------

A development shell makes available several code-formatting and quality checkers, which should be periodically run during the development process. See :doc:`Code Quality <code_quality>` for full details.

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
