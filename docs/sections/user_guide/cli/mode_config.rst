Mode ``config``
===============

The ``uw`` mode for handling configs.

.. code:: sh

  $ uw config --help
  usage: uw config [-h] MODE ...

  Handle configs

  Optional arguments:
    -h, --help
          Show help and exit

  Positional arguments:
    MODE
      compare
          Compare configs
      realize
          Realize config
      translate
          Translate configs
      validate
          Validate config

.. _compare_configs_cli_examples:

``compare``
-----------

.. code:: sh

  $ uw config compare --help
  usage: uw config compare --file-1-path PATH --file-2-path PATH [-h] [--file-1-format {ini,nml,sh,yaml}] [--file-2-format {ini,nml,sh,yaml}] [--quiet] [--verbose]

  Compare configs

  Required arguments:
    --file-1-path PATH
          Path to file 1
    --file-2-path PATH
          Path to file 2

  Optional arguments:
    -h, --help
          Show help and exit
    --file-1-format {ini,nml,sh,yaml}
          Format of file 1
    --file-2-format {ini,nml,sh,yaml}
          Format of file 2
    --quiet, -q
          Print no logging messages
    --verbose, -v
          Print all logging messages


Examples
~~~~~~~~

TBD

.. _realize_configs_cli_examples:

``realize``
-----------

.. code:: sh

  $ uw config realize --help
  usage: uw config realize --values-file PATH [-h] [--input-file PATH] [--input-format {ini,nml,sh,yaml}] [--output-file PATH] [--output-format {ini,nml,sh,yaml}] [--values-format {ini,nml,sh,yaml}]
                           [--values-needed] [--dry-run] [--quiet] [--verbose]

  Realize config

  Required arguments:
    --values-file PATH
          Path to file providing override or interpolation values

  Optional arguments:
    -h, --help
          Show help and exit
    --input-file PATH, -i PATH
          Path to input file (defaults to stdin)
    --input-format {ini,nml,sh,yaml}
          Input format
    --output-file PATH, -o PATH
          Path to output file (defaults to stdout)
    --output-format {ini,nml,sh,yaml}
          Output format
    --values-format {ini,nml,sh,yaml}
          Values format
    --values-needed
          Print report of values needed to render template
    --dry-run
          Only log info, making no changes
    --quiet, -q
          Print no logging messages
    --verbose, -v
          Print all logging messages

Examples
~~~~~~~~

TBD

.. _translate_configs_cli_examples:

``translate``
-------------

.. code:: sh

  $ uw config translate --help
  usage: uw config translate [-h] [--input-file PATH] [--input-format {atparse}] [--output-file PATH] [--output-format {jinja2}] [--dry-run] [--quiet] [--verbose]

  Translate configs

  Optional arguments:
    -h, --help
          Show help and exit
    --input-file PATH, -i PATH
          Path to input file (defaults to stdin)
    --input-format {atparse}
          Input format
    --output-file PATH, -o PATH
          Path to output file (defaults to stdout)
    --output-format {jinja2}
          Output format
    --dry-run
          Only log info, making no changes
    --quiet, -q
          Print no logging messages
    --verbose, -v
          Print all logging messages

Examples
~~~~~~~~

TBD

.. _validate_configs_cli_examples:

``validate``
------------

.. code:: sh

  $ uw config validate --help
  usage: uw config validate --schema-file PATH [-h] [--input-file PATH] [--quiet] [--verbose]

  Validate config

  Required arguments:
    --schema-file PATH
          Path to schema file to use for validation

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
