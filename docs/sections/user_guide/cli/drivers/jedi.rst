``jedi``
========

The ``uw`` mode for configuring and running the JEDI framework.

.. code-block:: text

    $ uw jedi -help
    usage: uw jedi [-h] [--version] TASK ...

    Execute JEDI tasks

    Optional arguments:
      -h, --help
          Show help and exit
      --version
          Show version info and exit

    Positional arguments:
      TASK
        configuration_file
          The configuration file
        files_copied
          Files copied for run
        files_linked
          Files linked for run
        provisioned_run_directory
          Run directory provisioned with all required content
        run
          A run
        runscript
          The runscript
        validate
          Validate the UW driver config
        validate_only
          Validate JEDI config YAML

All tasks take the same arguments. For example:

.. code-block:: text

   $ uw jedi run -help
   usage: uw jedi run --cycle CYCLE [-h] [--version] [--config-file PATH] [--batch] [--dry-run]
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
         Path to config file (default: read from stdin)
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
.. literalinclude:: ../../../../shared/jedi.yaml


Its contents are described in section :ref:`jedi_yaml`.

* Run ``jedi`` on an interactive node

   .. code-block:: text

      $ uw jedi run --config-file config.yaml

The driver creates a ``runscript.jedi`` file in the directory specified by ``run_dir:`` in the config and runs it, executing ``jedi``.

* Run ``jedi`` via a batch job

   .. code-block:: text

      $ uw jedi run --config-file config.yaml --batch

The driver creates a ``runscript.jedi`` file in the directory specified by ``run_dir:`` in the config and submits it to the batch system. Running with ``--batch`` requires a correctly configured ``platform:`` block in ``config.yaml``, as well as appropriate settings in the ``execution:`` block under ``jedi:``.

* Specifying the ``--dry-run`` flag results in the driver logging messages about actions it would have taken, without actually taking any.

  .. code-block:: text

     $ uw jedi run --config-file config.yaml --batch --dry-run
