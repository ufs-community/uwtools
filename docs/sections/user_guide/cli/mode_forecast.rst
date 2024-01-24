Mode ``forecast``
=================

The ``uw`` mode for configuring and running forecasts.

.. code-block:: text

   $ uw forecast --help
   usage: uw forecast [-h] MODE ...

   Configure and run forecasts

   Optional arguments:
     -h, --help
           Show help and exit

   Positional arguments:
     MODE
       run
           Run a forecast

``run``
-------

.. code-block:: text

   $ uw forecast run --help
   usage: uw forecast run --config-file PATH --cycle CYCLE --model {FV3} [-h] [--batch-script PATH]
                          [--dry-run] [--quiet] [--verbose]

   Run a forecast

   Required arguments:
     --config-file PATH, -c PATH
         Path to config file
     --cycle CYCLE
         The cycle in ISO8601 format
     --model {FV3}
         Model name

   Optional arguments:
     -h, --help
         Show help and exit
     --batch-script PATH
         Path to output batch file (defaults to stdout)
     --dry-run
         Only log info, making no changes
     --debug
         Print all log messages, plus any unhandled exception's stack trace (implies --verbose)
     --quiet, -q
         Print no logging messages
     --verbose, -v
         Print all logging messages

.. _cli_forecast_run_examples:

Examples
^^^^^^^^

The examples use a configuration file named ``config.yaml``. Its contents are described in depth in Section :ref:`forecast_yaml`.

* Run an FV3 forecast on an interactive node

  .. code-block:: sh

    $ uw forecast run -c config.yaml --cycle 2024-01-09T12 --model FV3

  The forecast will run on the node where you have invoked this command. Optionally, capture the output in a log file using shell redirection.

* Run an FV3 forecast using a batch system 

  .. code-block:: sh

    $ uw forecast run -c config.yaml --cycle 2024-01-09T12 --model FV3 --batch-script submit_fv3.sh

  This command writes a file named ``submit_fv3.sh`` and submits it to the batch system.

* With the ``--dry-run`` flag specified, nothing is written to ``stdout``, but a report of all the directories, files, symlinks, etc., that would have been created are logged to ``stderr``. None of these artifacts will actually be created and no jobs will be executed or submitted to the batch system.

  .. code-block:: sh

    $ uw forecast run -c config.yaml --cycle 2024-01-09T12 --model FV3 --batch-script --dry-run

* Request verbose log output

  .. code-block:: sh

    $ uw forecast run -c config.yaml --cycle 2024-01-09T12 --model FV3 -v
