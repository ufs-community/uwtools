``make_solo_mosaic``
====================

The ``uw`` mode for configuring and running the UFS Utils preprocessing component ``make_solo_mosaic``. Documentation for this UFS Utils component is :ufs-utils:`here <make-solo-mosaic>`.

.. code-block:: text

   $ uw make_solo_mosaic --help
   usage: uw make_solo_mosaic [-h] [--version] TASK ...

   Execute make_solo_mosaic tasks

   Optional arguments:
     -h, --help
         Show help and exit
     --version
         Show version info and exit

   Positional arguments:
     TASK
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

   $ uw make_solo_mosaic run --help
   usage: uw make_solo_mosaic run [-h] [--version] [--config-file PATH] [--batch] [--dry-run]
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
.. literalinclude:: ../../../../shared/make_solo_mosaic.yaml

Its contents are described in section :ref:`make_solo_mosaic_yaml`.

* Run ``make_solo_mosaic`` on an interactive node

  .. code-block:: text

     $ uw make_solo_mosaic run --config-file config.yaml

  The driver creates a ``runscript.make_solo_mosaic`` file in the directory specified by ``run_dir:`` in the config and runs it, executing ``make_solo_mosaic``.

* Run ``make_solo_mosaic`` via a batch job

  .. code-block:: text

     $ uw make_solo_mosaic run --config-file config.yaml --batch

  The driver creates a ``runscript.make_solo_mosaic`` file in the directory specified by ``run_dir:`` in the config and submits it to the batch system. Running with ``--batch`` requires a correctly configured ``platform:`` block in ``config.yaml``, as well as appropriate settings in the ``execution:`` block under ``make_solo_mosaic:``.

  Looking at the run command in ``runscript.make_solo_mosaic`` shows us the specified executable as well as the YAML keys converted to appropriate command line flags.

  .. code-block:: text

     time make_solo_mosaic --num_tiles 1 --dir /path/to/grid/ --tile_file C403_grid.tile7.halo6.nc --periodx 360 --periody 360

* Specifying the ``--dry-run`` flag results in the driver logging messages about actions it would have taken, without actually taking any.

  .. code-block:: text

     $ uw make_solo_mosaic run --config-file config.yaml --batch --dry-run
