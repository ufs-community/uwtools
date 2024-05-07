``shave``
=========

The ``uw`` mode for configuring and running the UFS Utils preprocessing component ``shave``. Documentation for this UFS Utils component is :ufs-utils:`here <shave>`.

.. code-block:: text

   $ uw shave --help
   usage: uw shave [-h] [--version] TASK ...

   Execute shave tasks

   Optional arguments:
     -h, --help
         Show help and exit
     --version
         Show version info and exit

   Positional arguments:
     TASK
       input_file
         Ensure the specified input grid file exists
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

   $ uw shave run --help
   usage: uw shave run --config-file PATH [-h] [--version] [--batch] [--dry-run]
                                    [--graph-file PATH] [--quiet] [--verbose]

   A run

   Required arguments:
     --config-file PATH, -c PATH
         Path to config file

   Optional arguments:
     -h, --help
         Show help and exit
     --version
         Show version info and exit
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
.. literalinclude:: ../../../../shared/shave.yaml
Its contents are described in section :ref:`shave_yaml`.

* Run ``shave`` on an interactive node

  .. code-block:: text

     $ uw shave run --config-file config.yaml

  The driver creates a ``runscript.shave`` file in the directory specified by ``run_dir:`` in the config and runs it, executing ``shave``.

* Run ``shave`` via a batch job

  .. code-block:: text

     $ uw shave run --config-file config.yaml --batch

  The driver creates a ``runscript.shave`` file in the directory specified by ``run_dir:`` in the config and submits it to the batch system. Running with ``--batch`` requires a correctly configured ``platform:`` block in ``config.yaml``, as well as appropriate settings in the ``execution:`` block under ``shave:``.

* Specifying the ``--dry-run`` flag results in the driver logging messages about actions it would have taken, without actually taking any.

  .. code-block:: text

     $ uw shave run --config-file config.yaml --batch --dry-run
