Mode ``sfc_climo_gen``
======================

The ``uw`` mode for configuring and running the :sfc-climo-gen:`sfc_climo_gen<>` component.

.. code-block:: text

   $ uw sfc_climo_gen --help
   usage: uw sfc_climo_gen [-h] TASK ...
   
   Execute sfc_climo_gen tasks
   
   Optional arguments:
     -h, --help
         Show help and exit
   
   Positional arguments:
     TASK
       namelist_file
         The namelist file
       provisioned_run_directory
         Run directory provisioned with all required content
       run
         Run execution
       runscript
         The runscript

All tasks take the same arguments. For example:

.. code-block:: text

   $ uw sfc_climo_gen run --help
   usage: uw sfc_climo_gen run --config-file PATH [-h] [--batch] [--dry-run] [--debug] [--quiet]
                               [--verbose]
   
   Run execution
   
   Required arguments:
     --config-file PATH, -c PATH
         Path to config file
   
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

The examples use a configuration file named ``config.yaml`` with content similar to:

.. highlight:: yaml
.. literalinclude:: ../../../shared/sfc_climo_gen.yaml

Its contents are described in depth in section :ref:`sfc_climo_gen_yaml`.
