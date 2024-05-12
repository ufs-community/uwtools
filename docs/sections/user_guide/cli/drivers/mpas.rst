``mpas``
==========

The ``uw`` mode for configuring and running the MPAS forecast model. Each listed ``TASK`` may be called to generate the runtime asset(s) it is responsible for, and will call any task it depends on as needed. A ``provisioned_run_directory`` comprises everything needed for a run, and a ``run`` runs the MPAS executable.

.. code-block:: text

   $ uw mpas --help
   usage: uw mpas [-h] [--version] TASK ...

   Execute mpas tasks

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

   $ uw mpas run --help
   usage: uw mpas run --cycle CYCLE [-h] [--version] [--config-file PATH] [--batch] [--dry-run]
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
.. literalinclude:: ../../../../shared/mpas.yaml

Its contents are described in depth in section :ref:`mpas_yaml`.

* Run MPAS on an interactive node

  .. code-block:: text

     $ uw mpas run --config-file config.yaml --cycle 2025-02-12T12

  The driver creates a ``runscript.mpas`` file in the directory specified by ``run_dir:`` in the config and runs it, executing ``atmosphere_model``.

* Run ``mpas`` via a batch job

  .. code-block:: text

     $ uw mpas run --config-file config.yaml --cycle 2025-02-12T12 --batch

  The driver creates a ``runscript.mpas`` file in the directory specified by ``run_dir:`` in the config and submits it to the batch system. Running with ``--batch`` requires a correctly configured ``platform:`` block in ``config.yaml``, as well as appropriate settings in the ``execution:`` block under ``mpas:``.

* Specifying the ``--dry-run`` flag results in the driver logging messages about actions it would have taken, without actually taking any.

  .. code-block:: text

     $ uw mpas run --config-file config.yaml --cycle 2025-02-12T12 --batch --dry-run

* The ``run`` task depends on the other available tasks and executes them as prerequisites. It is possible to execute any task directly, which entails execution of any of *its* dependencies. For example, to create an ``mpas`` run directory provisioned with all the files, directories, symlinks, etc. required per the configuration file:

  .. code-block:: text

     $ uw mpas provisioned_run_directory --config-file config.yaml --cycle 2025-02-12T12 --batch
