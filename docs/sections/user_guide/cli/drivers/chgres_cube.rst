``chgres_cube``
===============

The ``uw`` mode for configuring and running the :ufs-utils:`chgres_cube<chgres-cube>` component.

.. code-block:: text

   $ uw chgres_cube --help
   usage: uw chgres_cube [-h] [--version] TASK ...

   Execute chgres_cube tasks

   Optional arguments:
     -h, --help
         Show help and exit
     --version
         Show version info and exit

   Positional arguments:
     TASK
       namelist_file
         The namelist file
       provisioned_run_directory
         Run directory provisioned with all required content
       run
         A run
       runscript
         The runscript
       validate
         Validate the UW driver config

All tasks take the same arguments. For example:

.. code-block:: text

   $ uw chgres_cube run --help
   usage: uw chgres_cube run --cycle CYCLE [-h] [--version] [--config-file PATH] [--batch]
                             [--dry-run] [--graph-file PATH] [--quiet] [--verbose]

   A run

   Required arguments:
     --cycle CYCLE
         The cycle in ISO8601 format

   Optional arguments:
     -h, --help
         Show help and exit
     --version
         Show version info and exit
     --config-file PATH, -c PATH
         Path to UW YAML config file (default: read from stdin)
     --batch
         Submit run to batch scheduler
     --dry-run
         Only log info, making no changes
     --graph-file PATH
         Path to Graphviz DOT output [experimental]
     --quiet, -q
         Print no logging messages
     --verbose, -v
         Print all logging messages

Examples
^^^^^^^^

The examples use a configuration file named ``config.yaml`` with content similar to:

.. highlight:: yaml
.. literalinclude:: ../../../../shared/chgres_cube.yaml

Its contents are described in depth in section :ref:`chgres_cube_yaml`. Each of the values in the ``chgres_cube`` YAML may contain Jinja2 variables/expressions using a ``cycle`` variable, which is a Python ``datetime`` object corresponding to the FV3 cycle being run.

* Run ``chgres_cube`` on an interactive node

  .. code-block:: text

     $ uw chgres_cube run --config-file config.yaml --cycle 2023-12-15T18

  The driver creates a ``runscript.chgres_cube`` file in the directory specified by ``run_dir:`` in the config and runs it, executing ``chgres_cube``.

* Run ``chgres_cube`` via a batch job

  .. code-block:: text

     $ uw chgres_cube run --config-file config.yaml --cycle 2023-12-15T18 --batch

  The driver creates a ``runscript.chgres_cube`` file in the directory specified by ``run_dir:`` in the config and submits it to the batch system. Running with ``--batch`` requires a correctly configured ``platform:`` block in ``config.yaml``, as well as appropriate settings in the ``execution:`` block under ``chgres_cube:``.

* Specifying the ``--dry-run`` flag results in the driver logging messages about actions it would have taken, without actually taking any.

  .. code-block:: text

     $ uw chgres_cube run --config-file config.yaml --cycle 2023-12-15T18 --batch --dry-run

* The ``run`` task depends on the other available tasks and executes them as prerequisites. It is possible to execute any task directly, which entails execution of any of *its* dependencies. For example, to create a ``chgres_cube`` run directory provisioned with all the files, directories, symlinks, etc. required per the configuration file:

  .. code-block:: text

     $ uw chgres_cube provisioned_run_directory --config-file config.yaml --cycle 2023-12-15T18 --batch

