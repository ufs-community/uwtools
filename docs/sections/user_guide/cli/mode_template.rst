Mode ``template``
=================

The ``uw`` mode for handling :jinja2:`Jinja2 templates<templates>`.

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

.. _template_cli_examples:

``render``
----------

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

The examples that follow use template file ``template`` with content

.. code:: sh

  {{ greeting }}, {{ recipient }}!

and YAML file ``values.yaml`` with content

.. code:: sh

  greeting: Hello
  recipient: World

* Show the values needed to render the template:

  .. code:: sh

    $ uw template render --input-file template --values-needed
    [2023-12-18T19:16:08]     INFO Value(s) needed to render this template are:
    [2023-12-18T19:16:08]     INFO greeting
    [2023-12-18T19:16:08]     INFO recipient

* Render the template to ``stdout``:

  .. code:: sh

    $ uw template render --input-file template --values-file values.yaml
    Hello, World!

  Shell redirection via ``|``, ``>``, et al may also be used to stream output to a file, another process, etc.

* Render the template to a file via command-line argument:

  .. code:: sh

    $ uw template render --input-file template --values-file values.yaml --output-file rendered

  The content of ``rendered``:

  .. code:: sh

    Hello, World!

* With the ``--dry-run`` flag specified, nothing is written to ``stdout`` (or to a file if ``--output-file`` is specified), but a report of what would have been written is logged to ``stderr``:

  .. code:: sh

    $ uw template render --input-file template --values-file values.yaml --dry-run
    [2023-12-18T19:38:15]     INFO Hello, World!

* Read the template from ``stdin`` and render to ``stdout``:

  .. code:: sh

    $ cat template | uw template render --values-file values.yaml
    Hello, World!

* If the values file has an unrecognized (or no) extension, ``uw`` will not know how to parse its content:

  .. code:: sh

    $ uw template render --input-file template --values-file values.txt
    Cannot deduce format of 'values.txt' from unknown extension 'txt'

  In this case, the format can be explicitly specified:

  .. code:: sh

    $ uw template render --input-file template --values-file values.txt --values-format yaml
    Hello, World!

* It is an error to render a template without providing all needed values. For example, with ``recipient: World`` removed from ``values.yaml``:

  .. code:: sh

    $ uw template render --input-file template --values-file values.yaml
    [2023-12-18T19:30:05]    ERROR Required value(s) not provided:
    [2023-12-18T19:30:05]    ERROR recipient

  But values may be supplemented by ``key=value`` command-line arguments, e.g.

  .. code:: sh

    $ uw template render --input-file template --values-file values.yaml recipient=Reader
    Hello, Reader!

  Such ``key=value`` arguments may also be used to *override* file-based values

  .. code:: sh

    $ uw template render --input-file template --values-file values.yaml recipient=Reader greeting="Good day"
    Good day, Reader!

* Request verbose log output:

  .. code:: sh

    $ uw template render --input-file template --values-file values.yaml --verbose
    [2023-12-18T23:25:01]    DEBUG Command: uw template render --input-file template --values-file values.yaml --verbose
    [2023-12-18T23:25:01]    DEBUG Internal arguments:
    [2023-12-18T23:25:01]    DEBUG ---------------------------------------------------------------------
    [2023-12-18T23:25:01]    DEBUG           values: values.yaml
    [2023-12-18T23:25:01]    DEBUG    values_format: yaml
    [2023-12-18T23:25:01]    DEBUG       input_file: template
    [2023-12-18T23:25:01]    DEBUG      output_file: None
    [2023-12-18T23:25:01]    DEBUG        overrides: {}
    [2023-12-18T23:25:01]    DEBUG    values_needed: False
    [2023-12-18T23:25:01]    DEBUG          dry_run: False
    [2023-12-18T23:25:01]    DEBUG ---------------------------------------------------------------------
    [2023-12-18T23:25:01]    DEBUG Read initial values from values.yaml
    Hello, World!

  Note that ``uw`` logs to ``stderr`` and writes non-log output to ``stdout``, so the streams can be redirected separately:

  .. code:: sh

    $ uw template render --input-file template --values-file values.yaml --verbose >rendered 2>rendered.log

  The content of ``rendered``:

  .. code:: sh

    Hello, World!

  The content of ``rendered.log``:

  .. code:: sh

    [2023-12-18T23:27:04]    DEBUG Command: uw template render --input-file template --values-file values.yaml --verbose
    [2023-12-18T23:27:04]    DEBUG Internal arguments:
    [2023-12-18T23:27:04]    DEBUG ---------------------------------------------------------------------
    [2023-12-18T23:27:04]    DEBUG           values: values.yaml
    [2023-12-18T23:27:04]    DEBUG    values_format: yaml
    [2023-12-18T23:27:04]    DEBUG       input_file: template
    [2023-12-18T23:27:04]    DEBUG      output_file: None
    [2023-12-18T23:27:04]    DEBUG        overrides: {}
    [2023-12-18T23:27:04]    DEBUG    values_needed: False
    [2023-12-18T23:27:04]    DEBUG          dry_run: False
    [2023-12-18T23:27:04]    DEBUG ---------------------------------------------------------------------
    [2023-12-18T23:27:04]    DEBUG Read initial values from values.yaml

* Non-YAML-formatted files may also be used as values sources. For example, ``template``

  .. code:: sh

    {{ values.greeting }}, {{ values.recipient }}!

  can be rendered with ``values.nml``

  .. code:: sh

    &values
      greeting = "Hello"
      recipient = "World"
    /

  like so:

  .. code:: sh

    $ uw template render --input-file template --values-file values.nml
    Hello, World!

  Note that ``ini`` and ``nml`` configs are, by definition, depth-2 configs, while ``sh`` configs are depth-1 and ``yaml`` configs have arbitrary depth.
