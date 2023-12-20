Mode ``rocoto``
===============

The ``uw`` mode for realizing and validating Rocoto XML documents

.. code:: sh

  $ uw rocoto --help
  usage: uw rocoto [-h] MODE ...

  Realize and validate Rocoto XML Documents

  Optional arguments:
    -h, --help
          Show help and exit

  Positional arguments:
    MODE
      realize
          Realize a Rocoto XML workflow document
      validate
          Validate Rocoto XML

.. _realize_rocoto_cli_examples:

``realize``
-----------

.. code:: sh

  $ uw rocoto realize --help
  usage: uw rocoto realize [-h] [--input-file PATH] [--output-file PATH] [--quiet] [--verbose]

  Realize a Rocoto XML workflow document

  Optional arguments:
    -h, --help
          Show help and exit
    --input-file PATH, -i PATH
          Path to input file (defaults to stdin)
    --output-file PATH, -o PATH
          Path to output file (defaults to stdout)
    --quiet, -q
          Print no logging messages
    --verbose, -v
          Print all logging messages

Examples
~~~~~~~~

TBD

.. _validate_rocoto_cli_examples:

``validate``
------------

.. code:: sh

  $ uw rocoto validate --help
  usage: uw rocoto validate [-h] [--input-file PATH] [--quiet] [--verbose]

  Validate Rocoto XML

  Optional arguments:
    -h, --help
          Show help and exit
    --input-file PATH, -i PATH
          Path to input file (defaults to stdin)
    --quiet, -q
          Print no logging messages
    --verbose, -v
          Print all logging messages

Examples
~~~~~~~~

TBD
