Mode ``forecast``
=================

The ``uw`` mode for configuring and running forecasts.

.. code:: sh

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

Submode ``run``
---------------

.. code:: sh

  $ uw forecast run --help
  usage: uw forecast run --config-file PATH --cycle CYCLE --model {FV3} [-h] [--batch-script PATH] [--dry-run] [--quiet] [--verbose]

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
    --quiet, -q
          Print no logging messages
    --verbose, -v
          Print all logging messages

Examples
~~~~~~~~

TBD
