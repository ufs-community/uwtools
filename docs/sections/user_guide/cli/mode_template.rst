Mode ``template``
=================

The ``uw`` mode for handling (`Jinja2 <https://palletsprojects.com/p/jinja/>`_) templates.

.. code:: sh

  $ uw template --help
  usage: uw template [-h] MODE ...

  Handle templates

  Optional arguments:
   -h, --help
         Show help and exit

  Positional arguments:
   MODE
     render
         Render a template

Submode ``render``
------------------

.. code:: sh

  $ uw template render --help
  usage: uw template render [-h] [--input-file PATH] [--output-file PATH] [--values-file PATH] [--values-format {ini,nml,sh,yaml}] [--values-needed] [--dry-run] [--quiet] [--verbose] [KEY=VALUE ...]

  Render a template

  Optional arguments:
   -h, --help
         Show help and exit
   --input-file PATH, -i PATH
         Path to input file (defaults to stdin)
   --output-file PATH, -o PATH
         Path to output file (defaults to stdout)
   --values-file PATH
         Path to file providing override or interpolation values
   --values-format {ini,nml,sh,yaml}
         Values format
   --values-needed
         Print report of values needed to render template
   --dry-run
         Only log info, making no changes
   KEY=VALUE
         A key=value pair to override/supplement config
   --quiet, -q
         Print no logging messages
   --verbose, -v
         Print all logging messages

Examples
~~~~~~~~

TBD
