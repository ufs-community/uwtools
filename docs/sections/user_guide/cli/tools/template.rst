``template``
============

The ``uw`` mode for handling :jinja2:`Jinja2 templates<templates>`.

.. code-block:: text

   $ uw template --help
   usage: uw template [-h] [--version] ACTION ...

   Handle templates

   Optional arguments:
     -h, --help
         Show help and exit
     --version
         Show version info exit

   Positional arguments:
     ACTION
       render
         Render a template
       translate
         Translate atparse to Jinja2

.. _cli_template_render_examples:

``render``
----------

.. code-block:: text

   $ uw template render --help
   usage: uw template render [-h] [--version] [--input-file PATH] [--output-file PATH]
                             [--values-file PATH] [--values-format {ini,nml,sh,yaml}] [--env]
                             [--search-path PATH[:PATH:...]] [--values-needed] [--partial]
                             [--dry-run] [--quiet] [--verbose]
                             [KEY=VALUE ...]

   Render a template

   Optional arguments:
     -h, --help
         Show help and exit
     --version
         Show version info exit
     --input-file PATH, -i PATH
         Path to input file (defaults to stdin)
     --output-file PATH, -o PATH
         Path to output file (defaults to stdout)
     --values-file PATH
         Path to file providing override or interpolation values
     --values-format {ini,nml,sh,yaml}
         Values format
     --env
         Use environment variables
     --search-path PATH[:PATH:...]
         Colon-separated paths to search for extra templates
     --values-needed
         Print report of values needed to render template
     --partial
         Permit partial template rendering
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

The examples in this section use a template file named ``template`` with the following contents:

.. code-block:: jinja

   {{ greeting }}, {{ recipient }}!

and a YAML file called ``values.yaml`` with the following contents:

.. code-block:: yaml

   greeting: Hello
   recipient: World

* To show the values needed to render the template:

  .. code-block:: text

     $ uw template render --input-file template --values-needed
     [2023-12-18T19:16:08]     INFO Value(s) needed to render this template are:
     [2023-12-18T19:16:08]     INFO   greeting
     [2023-12-18T19:16:08]     INFO   recipient

* To render the template to ``stdout``:

  .. code-block:: text

     $ uw template render --input-file template --values-file values.yaml
     Hello, World!

  Shell redirection via ``|``, ``>``, et al. may also be used to stream output to a file, another process, etc.

* To render the template to a file via command-line argument:

  .. code-block:: text

     $ uw template render --input-file template --values-file values.yaml --output-file rendered

  The content of ``rendered``:

  .. code-block:: text

     Hello, World!

* With the ``--dry-run`` flag specified, nothing is written to ``stdout`` (or to a file if ``--output-file`` is specified), but a report of what would have been written is logged to ``stderr``:

  .. code-block:: text

     $ uw template render --input-file template --values-file values.yaml --dry-run
     [2023-12-18T19:38:15]     INFO Hello, World!

* To read the template from ``stdin`` and render to ``stdout``:

  .. code-block:: text

     $ cat template | uw template render --values-file values.yaml
     Hello, World!

* If the values file has an unrecognized (or no) extension, ``uw`` will not know how to parse its contents:

  .. code-block:: text

     $ uw template render --input-file template --values-file values.txt
     Cannot deduce format of 'values.txt' from unknown extension 'txt'

  In this case, the format can be explicitly specified:

  .. code-block:: text

     $ uw template render --input-file template --values-file values.txt --values-format yaml
     Hello, World!

* To request verbose log output:

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

  If additional information is needed, ``--debug`` can be used which will return the stack trace from any unhandled exception as well.

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

* **NB**: This set of examples is based on a ``values.yaml`` file with ``recipient: World`` removed.

  It is an error to render a template without providing all needed values.

  .. code-block:: text

   $ uw template render --input-file template --values-file values.yaml
   [2024-03-02T16:42:48]    ERROR Required value(s) not provided:
   [2024-03-02T16:42:48]    ERROR   recipient
   [2024-03-02T16:42:48]    ERROR Template could not be rendered.

  But the ``--partial`` switch may be used to render as much as possible while passing expressions containing missing values through unchanged:

  .. code-block:: text

     $ uw template render --input-file template --values-file values.yaml --partial
     Hello, {{ recipient }}!

  Values may also be supplemented by ``key=value`` command-line arguments:

  .. code-block:: text

     $ uw template render --input-file template --values-file values.yaml recipient=Reader
     Hello, Reader!

  The optional ``-env`` switch allows environment variables to be used to supply values:

  .. code-block:: text

     $ export recipient=You
     $ uw template render --input-file template --values-file values.yaml --env
     Hello, You!

  Values from ``key=value`` arguments override values from file, and environment variables override both:

  .. code-block:: text

     $ recipient=Sunshine uw template render --input-file template --values-file values.yaml recipient=Reader greeting="Good day" --env
     Good day, Sunshine!

  Note that ``recipient=Sunshine`` is shell syntax for exporting environment variable ``recipient`` only for the duration of the command that follows. It should not be confused with the two ``key=value`` pairs later on the command line, which are arguments to ``uw``.

* Jinja2 supports references to additional templates via, for example, `import <https://jinja.palletsprojects.com/en/latest/templates/#import>`_ expressions, and ``uw`` provides support as follows:

  #. By default, the directory containing the primary template file is used as the search path for additional templates.
  #. The optional ``--search-path`` flag overrides the default search path with any number of explicitly specified, colon-separated paths.

  For example, given file ``template``

  .. code-block:: text

     {% import "macros" as m -%}
     {{ m.double(11) }}

  and file ``macros`` (in the same directory as ``template``)

  .. code-block:: text

     {% macro double(n) -%}
     {{ n * 2 }}
     {%- endmacro %}

  the template is rendered as

  .. code-block:: text

     $ uw template render --input-file template
     22

  The invocation ``uw template render --input-file template --search-path $PWD`` would behave identically. Alternatively, ``--search-path`` could be specified with a colon-separated set of directories to be searched for templates.

  **NB**: Reading the primary template from ``stdin`` requires use of ``--search-path``, as there is no implicit directory related to the input. For example, given the existence of ``/path/to/macros``:

  .. code-block:: text

     $ cat template | uw template render --search-path /path/to
     22

* Non-YAML-formatted files may also be used as value sources. For example, ``template``

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

.. _cli_template_translate_examples:

``translate``
-------------

.. code-block:: text

   $ uw template translate --help
   usage: uw template translate [-h] [--version] [--input-file PATH] [--output-file PATH] [--dry-run]
                                [--quiet] [--verbose]

   Translate atparse to Jinja2

   Optional arguments:
     -h, --help
         Show help and exit
     --version
         Show version info exit
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

The examples in this section use atparse-formatted template file ``atparse.txt`` with the following contents:

.. code-block:: text

   @[greeting], @[recipient]!

* To convert an atparse-formatted template file to Jinja2 format:

  .. code-block:: text

     $ uw template translate --input-file atparse.txt
     {{ greeting }}, {{ recipient }}!

  Shell redirection via ``|``, ``>``, et al. may also be used to stream output to a file, another process, etc.

* To convert the template to a file via command-line argument:

  .. code-block:: text

     $ uw template translate --input-file atparse.txt --output-file jinja2.txt

  The content of ``jinja2.txt``:

  .. code-block:: jinja

     {{ greeting }}, {{ recipient }}!

* With the ``--dry-run`` flag specified, nothing is written to ``stdout`` (or to a file if ``--output-file`` is specified), but a report of what would have been written is logged to ``stderr``:

  .. code-block:: text

     $ uw template translate --input-file atparse.txt --dry-run
     [2024-02-06T21:53:43]     INFO {{ greeting }}, {{ recipient }}!
