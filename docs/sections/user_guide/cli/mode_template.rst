Mode ``template``
=================

The ``uw`` mode for handling :jinja2:`Jinja2 templates<templates>`.

.. code-block:: text

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
       translate
         Translate atparse to Jinja2

.. _cli_template_render_examples:

``render``
----------

.. code-block:: text

   $ uw template render --help
   usage: uw template render [-h] [--input-file PATH] [--output-file PATH] [--values-file PATH]
                             [--values-format {ini,nml,sh,yaml}] [--values-needed] [--dry-run]
                             [--quiet] [--verbose]
                             [KEY=VALUE ...]

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
     --quiet, -q
         Print no logging messages
     --verbose, -v
         Print all logging messages
     KEY=VALUE
         A key=value pair to override/supplement config

Examples
^^^^^^^^

The examples that follow use template file ``template`` with content

.. code-block:: jinja

   {{ greeting }}, {{ recipient }}!

and YAML file ``values.yaml`` with content

.. code-block:: yaml

   greeting: Hello
   recipient: World

* Show the values needed to render the template:

  .. code-block:: text

     $ uw template render --input-file template --values-needed
     [2023-12-18T19:16:08]     INFO Value(s) needed to render this template are:
     [2023-12-18T19:16:08]     INFO greeting
     [2023-12-18T19:16:08]     INFO recipient

* Render the template to ``stdout``:

  .. code-block:: text

     $ uw template render --input-file template --values-file values.yaml
     Hello, World!

  Shell redirection via ``|``, ``>``, et al may also be used to stream output to a file, another process, etc.

* Render the template to a file via command-line argument:

  .. code-block:: text

     $ uw template render --input-file template --values-file values.yaml --output-file rendered

  The content of ``rendered``:

  .. code-block:: text

     Hello, World!

* With the ``--dry-run`` flag specified, nothing is written to ``stdout`` (or to a file if ``--output-file`` is specified), but a report of what would have been written is logged to ``stderr``:

  .. code-block:: text

     $ uw template render --input-file template --values-file values.yaml --dry-run
     [2023-12-18T19:38:15]     INFO Hello, World!

* Read the template from ``stdin`` and render to ``stdout``:

  .. code-block:: text

     $ cat template | uw template render --values-file values.yaml
     Hello, World!

* If the values file has an unrecognized (or no) extension, ``uw`` will not know how to parse its content:

  .. code-block:: text

     $ uw template render --input-file template --values-file values.txt
     Cannot deduce format of 'values.txt' from unknown extension 'txt'

  In this case, the format can be explicitly specified:

  .. code-block:: text

     $ uw template render --input-file template --values-file values.txt --values-format yaml
     Hello, World!

* It is an error to render a template without providing all needed values. For example, with ``recipient: World`` removed from ``values.yaml``:

  .. code-block:: text

     $ uw template render --input-file template --values-file values.yaml
     [2023-12-18T19:30:05]    ERROR Required value(s) not provided:
     [2023-12-18T19:30:05]    ERROR recipient

  But values may be supplemented by ``key=value`` command-line arguments, e.g.

  .. code-block:: text

     $ uw template render --input-file template --values-file values.yaml recipient=Reader
     Hello, Reader!

  Such ``key=value`` arguments may also be used to *override* file-based values

  .. code-block:: text

     $ uw template render --input-file template --values-file values.yaml recipient=Reader greeting="Good day"
     Good day, Reader!

* Request verbose log output:

  .. code-block:: text

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

  .. code-block:: text

     $ uw template render --input-file template --values-file values.yaml --verbose >rendered 2>rendered.log

  The content of ``rendered``:

  .. code-block:: text

     Hello, World!

  The content of ``rendered.log``:

  .. code-block:: text

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

  .. code-block:: jinja

     {{ values.greeting }}, {{ values.recipient }}!

  can be rendered with ``values.nml``

  .. code-block:: fortran

     &values
       greeting = "Hello"
       recipient = "World"
     /

  like so:

  .. code-block:: text

     $ uw template render --input-file template --values-file values.nml
     Hello, World!

  Note that ``ini`` and ``nml`` configs are, by definition, depth-2 configs, while ``sh`` configs are depth-1 and ``yaml`` configs have arbitrary depth.

.. _cli_template_translate_examples:

``translate``
-------------

.. code-block:: text

   $ uw template translate --help
   usage: uw template translate [-h] [--input-file PATH] [--output-file PATH] [--dry-run] [--quiet]
                                [--verbose]

   Translate atparse to Jinja2

   Optional arguments:
     -h, --help
         Show help and exit
     --input-file PATH, -i PATH
         Path to input file (defaults to stdin)
     --output-file PATH, -o PATH
         Path to output file (defaults to stdout)
     --dry-run
         Only log info, making no changes
     --quiet, -q
         Print no logging messages
     --verbose, -v
         Print all logging messages

Examples
^^^^^^^^

The examples that follow use atparse-formatted template file ``atparse.txt`` with content

.. code-block:: text

   @[greeting], @[recipient]!

* Convert an atparse-formatted template file to Jinja2 format:

  .. code-block:: text

     $ uw template translate --input-file atparse.txt
     {{greeting}}, {{recipient}}!

  Shell redirection via ``|``, ``>``, et al may also be used to stream output to a file, another process, etc.

* Convert the template to a file via command-line argument:

  .. code-block:: text

     $ uw template translate --input-file atparse.txt --output-file jinja2.txt

  The content of ``jinja2.txt``:

  .. code-block:: jinja

     {{greeting}}, {{recipient}}!

* With the ``--dry-run`` flag specified, nothing is written to ``stdout`` (or to a file if ``--output-file`` is specified), but a report of what would have been written is logged to ``stderr``:

  .. code-block:: text

     $ uw template translate --input-file atparse.txt --dry-run
     [2024-01-03T16:41:13]     INFO {{greeting}}, {{recipient}}!

* If an input is read alone from ``stdin``, ``uw`` will not know how to parse its content as we must always specify the formats:

  .. code-block:: text

     $ cat atparse.txt | uw template translate
     {{greeting}}, {{recipient}}!
