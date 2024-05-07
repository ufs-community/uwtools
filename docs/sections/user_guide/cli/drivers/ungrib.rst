``ungrib``
==========

The ``uw`` mode for configuring and running the WRF preprocessing component ``ungrib``.

.. code-block:: text

   $ uw ungrib --help
   usage: uw ungrib [-h] [--version] TASK ...

   Execute Ungrib tasks

   Optional arguments:
     -h, --help
         Show help and exit
     --version
         Show version info and exit

   Positional arguments:
     TASK
       gribfile
         A symlink to the input GRIB file
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
       vtable
         A symlink to the Vtable file

All tasks take the same arguments. For example:

.. code-block:: text

   $ uw ungrib run --help
   usage: uw ungrib run --cycle CYCLE [-h] [--version] [--config-file PATH] [--batch] [--dry-run]
                        [--graph-file PATH] [--quiet] [--verbose]

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
.. literalinclude:: ../../../../shared/ungrib.yaml

Its contents are described in depth in section :ref:`ungrib_yaml`.

* Run ``ungrib`` on an interactive node

  .. code-block:: text

     $ uw ungrib run --config-file config.yaml --cycle 2021-04-01T12

  The driver creates a ``runscript.ungrib`` file in the directory specified by ``run_dir:`` in the config and runs it, executing ``ungrib``.

* Run ``ungrib`` via a batch job

  .. code-block:: text

     $ uw ungrib run --config-file config.yaml --cycle 2021-04-01T12 --batch

  The driver creates a ``runscript.ungrib`` file in the directory specified by ``run_dir:`` in the config and submits it to the batch system. Running with ``--batch`` requires a correctly configured ``platform:`` block in ``config.yaml``, as well as appropriate settings in the ``execution:`` block under ``ungrib:``.

* Specifying the ``--dry-run`` flag results in the driver logging messages about actions it would have taken, without actually taking any.

  .. code-block:: text

     $ uw ungrib run --config-file config.yaml --cycle 2021-04-01T12 --batch --dry-run

* The ``run`` task depends on the other available tasks and executes them as prerequisites. It is possible to execute any task directly, which entails execution of any of *its* dependencies. For example, to create an ``ungrib`` run directory provisioned with all the files, directories, symlinks, etc. required per the configuration file:

  .. code-block:: text

     $ uw ungrib provisioned_run_directory --config-file config.yaml --cycle 2021-04-01T12 --batch
