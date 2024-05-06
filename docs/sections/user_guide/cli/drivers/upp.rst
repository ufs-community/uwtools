``upp``
=======

The ``uw`` mode for configuring and running the `UPP <https://epic.noaa.gov/unified-post-processor/>`_ component.

.. code-block:: text

   $ uw upp --help
   usage: uw upp [-h] [--version] TASK ...

   Execute upp tasks

   Optional arguments:
     -h, --help
         Show help and exit
     --version
         Show version info and exit

   Positional arguments:
     TASK
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
       validate
         Validate the UW driver config

All tasks take the same arguments. For example:

.. code-block:: text

   $ uw upp run --help
   usage: uw upp run --cycle CYCLE --leadtime LEADTIME [-h] [--version] [--config-file PATH]
                     [--batch] [--dry-run] [--graph-file PATH] [--quiet] [--verbose]

   A run

   Required arguments:
     --cycle CYCLE
         The cycle in ISO8601 format
     --leadtime LEADTIME
         Leadtime in hours

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
.. literalinclude:: ../../../../shared/upp.yaml

Its contents are described in depth in section :ref:`upp_yaml`.

* Run ``upp`` on an interactive node

  .. code-block:: text

     $ uw upp run --config-file config.yaml --cycle 2024-05-06T12 --leadtime 6

  The driver creates a ``runscript.upp`` file in the directory specified by ``run_dir:`` in the config and runs it, executing ``upp``.

* Run ``upp`` via a batch job

  .. code-block:: text

     $ uw upp run --config-file config.yaml --cycle 2024-05-06T12 --leadtime 6 --batch

  The driver creates a ``runscript.upp`` file in the directory specified by ``run_dir:`` in the config and submits it to the batch system. Running with ``--batch`` requires a correctly configured ``platform:`` block in ``config.yaml``, as well as appropriate settings in the ``execution:`` block under ``upp:``.

* Specifying the ``--dry-run`` flag results in the driver logging messages about actions it would have taken, without actually taking any.

  .. code-block:: text

     $ uw upp run --config-file config.yaml --cycle 2024-05-06T12 --leadtime 6 --batch --dry-run

* The ``run`` task depends on the other available tasks and executes them as prerequisites. It is possible to execute any task directly, which entails execution of any of *its* dependencies. For example, to create an ``upp`` run directory provisioned with all the files, directories, symlinks, etc. required per the configuration file:

  .. code-block:: text

     $ uw upp provisioned_run_directory --config-file config.yaml --cycle 2024-05-06T12 --leadtime 6 --batch
