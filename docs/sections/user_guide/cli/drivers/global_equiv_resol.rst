``global_equiv_resol``
======================

The ``uw`` mode for configuring and running the UFS Utils preprocessing component ``global_equiv_resol``. Documentation for this UFS Utils component is :ufs-utils:`here <global-equiv-resol>`.

.. code-block:: text

   $ uw global_equiv_resol --help
   usage: uw global_equiv_resol [-h] [--version] TASK ...

   Execute global_equiv_resol tasks

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

   $ uw global_equiv_resol run --help
   usage: uw global_equiv_resol run [-h] [--version] [--config-file PATH] [--batch] [--dry-run]
                                    [--graph-file PATH] [--quiet] [--verbose]

   A run

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
.. literalinclude:: ../../../../shared/global_equiv_resol.yaml

Its contents are described in section :ref:`global_equiv_resol_yaml`.

* Run ``global_equiv_resol`` on an interactive node

  .. code-block:: text

     $ uw global_equiv_resol run --config-file config.yaml

  The driver creates a ``runscript.global_equiv_resol`` file in the directory specified by ``run_dir:`` in the config and runs it, executing ``global_equiv_resol``.

* Run ``global_equiv_resol`` via a batch job

  .. code-block:: text

     $ uw global_equiv_resol run --config-file config.yaml --batch

  The driver creates a ``runscript.global_equiv_resol`` file in the directory specified by ``run_dir:`` in the config and submits it to the batch system. Running with ``--batch`` requires a correctly configured ``platform:`` block in ``config.yaml``, as well as appropriate settings in the ``execution:`` block under ``global_equiv_resol:``.

* Specifying the ``--dry-run`` flag results in the driver logging messages about actions it would have taken, without actually taking any.

  .. code-block:: text

     $ uw global_equiv_resol run --config-file config.yaml --batch --dry-run

.. include:: ../../../../shared/key_path.rst
