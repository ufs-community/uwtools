``fv3``
=======

The ``uw`` mode for configuring and running FV3.

.. code-block:: text

   $ uw fv3 --help
   usage: uw fv3 [-h] TASK ...

   Execute FV3 tasks

   Optional arguments:
     -h, --help
         Show help and exit

   Positional arguments:
     TASK
       boundary_files
         Lateral boundary-condition files
       diag_table
         The diag_table file
       field_table
         The field_table file
       files_copied
         Files copied for run
       files_linked
         Files linked for run
       model_configure
         The model_configure file
       namelist_file
         The namelist file
       provisioned_run_directory
         Run directory provisioned with all required content
       restart_directory
         The RESTART directory
       run
         A run
       runscript
         The runscript

All tasks take the same arguments. For example:

.. code-block:: text

   $ uw fv3 run --help
   usage: uw fv3 run --config-file PATH --cycle CYCLE [-h] [--batch] [--dry-run] [--debug] [--quiet]
                     [--verbose]

   A run

   Required arguments:
     --config-file PATH, -c PATH
         Path to config file
     --cycle CYCLE
         The cycle in ISO8601 format

   Optional arguments:
     -h, --help
         Show help and exit
     --batch
         Submit run to batch scheduler
     --dry-run
         Only log info, making no changes
     --debug
         Print all log messages, plus any unhandled exception's stack trace (implies --verbose)
     --quiet, -q
         Print no logging messages
     --verbose, -v
         Print all logging messages

Examples
^^^^^^^^

The examples use a configuration file named ``config.yaml``. Its contents are described in depth in section :ref:`fv3_yaml`.

* Run FV3 on an interactive node

  .. code-block:: text

     $ uw fv3 run --config-file config.yaml --cycle 2024-02-11T12

  The driver creates a ``runscript`` file in the directory specified by ``run_dir:`` in the config and runs it, executing FV3.

* Run FV3 via a batch job

  .. code-block:: text

     $ uw fv3 run --config-file config.yaml --cycle 2024-02-11T12 --batch

  The driver creates a ``runscript`` file in the directory specified by ``run_dir:`` in the config and submits it to the batch system. Running with ``--batch`` requires a correctly configured ``platform:`` block in ``config.yaml``, as well as appropriate settings in the ``execution:`` block under ``fv3:``.

* Specifying the ``--dry-run`` flag results in the driver logging messages about actions it would have taken, without actually taking any.

  .. code-block:: text

     $ uw fv3 run --config-file config.yaml --cycle 2024-02-11T12 --batch --dry-run

* The ``run`` task depends on the other available tasks and executes them as prerequisites. It is possible to execute any task directly, which entails execution of any of *its* dependencies. For example, to create an FV3 run directory provisioned with all the files, directories, symlinks, etc. required per the configuration file:

  .. code-block:: text

     $ uw fv3 provisioned_run_directory --config-file config.yaml --cycle 2024-02-11T12 --batch
