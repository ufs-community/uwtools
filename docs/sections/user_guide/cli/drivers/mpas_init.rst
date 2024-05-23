``mpas_init``
=============

The ``uw`` mode for configuring and running the MPAS ``init_atmosphere`` tool. Each listed ``TASK`` may be called to generate the runtime asset(s) it is responsible for, and will call any task it depends on as needed. A ``provisioned_run_directory`` comprises everything needed for a run, and a ``run`` runs the ``init_atmosphere`` executable.

.. code-block:: text

   $ uw mpas_init --help
   usage: uw mpas_init [-h] [--version] TASK ...

   Execute mpas_init tasks

   Optional arguments:
     -h, --help
         Show help and exit
     --version
         Show version info and exit

   Positional arguments:
     TASK
       boundary_files
         Boundary files
       files_copied
         Files copied for run
       files_linked
         Files linked for run
       namelist_file
         The namelist file
       provisioned_run_directory
         Run directory provisioned with all required content
       run
         A run
       runscript
         The runscript
       streams_file
         The streams file
       validate
         Validate the UW driver config

All tasks take the same arguments. For example:

.. code-block:: text

   $ uw mpas_init run --help
   usage: uw mpas_init run --cycle CYCLE [-h] [--version] [--config-file PATH] [--batch] [--dry-run]
                           [--graph-file PATH] [--quiet] [--verbose]

   A run

   Required arguments:
     --cycle CYCLE
         The cycle in ISO8601 format (e.g. 2024-05-08T18)

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
.. literalinclude:: ../../../../shared/mpas_init.yaml

Its contents are described in depth in section :ref:`mpas_init_yaml`.

* Run ``init_atmosphere`` on an interactive node

  .. code-block:: text

     $ uw mpas_init run --config-file config.yaml --cycle 2023-12-18T00

  The driver creates a ``runscript.mpas_init`` file in the directory specified by ``run_dir:`` in the config and runs it, executing ``init_atmosphere``.

* Run ``init_atmosphere`` via a batch job

  .. code-block:: text

     $ uw mpas_init run --config-file config.yaml --cycle 2023-12-18T00 --batch

  The driver creates a ``runscript.mpas_init`` file in the directory specified by ``run_dir:`` in the config and submits it to the batch system. Running with ``--batch`` requires a correctly configured ``platform:`` block in ``config.yaml``, as well as appropriate settings in the ``execution:`` block under ``mpas_init:``.

* Specifying the ``--dry-run`` flag results in the driver logging messages about actions it would have taken, without actually taking any.

  .. code-block:: text

     $ uw mpas_init run --config-file config.yaml --cycle 2023-12-18T00 --batch --dry-run

.. include:: ../../../../shared/key_path.rst

* The ``run`` task depends on the other available tasks and executes them as prerequisites. It is possible to execute any task directly, which entails execution of any of *its* dependencies. For example, to create an ``mpas_init`` run directory provisioned with all the files, directories, symlinks, etc. required per the configuration file:

  .. code-block:: text

     $ uw mpas_init provisioned_run_directory --config-file config.yaml --cycle 2023-12-18T00 --batch
