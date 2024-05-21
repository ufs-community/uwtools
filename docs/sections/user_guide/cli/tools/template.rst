``template``
============

The ``uw`` mode for handling :jinja2:`Jinja2 templates<templates>`.

.. literalinclude:: template/help.cmd
   :language: text
   :emphasize-lines: 1
.. literalinclude:: template/help.out
   :language: text

.. _cli_template_render_examples:

``render``
----------

.. literalinclude:: template/render-help.cmd
   :language: text
   :emphasize-lines: 1
.. literalinclude:: template/render-help.out
   :language: text

Examples
^^^^^^^^

The examples in this section use a template file named ``template`` with the following contents:

.. literalinclude:: template/template
   :language: jinja

and a YAML file called ``values.yaml`` with the following contents:

.. literalinclude:: template/values.yaml
   :language: yaml

* To show the values needed to render the template:

  .. literalinclude:: template/render-exec-values-needed.cmd
     :language: text
     :emphasize-lines: 1
  .. literalinclude:: template/render-exec-values-needed.out
     :language: text

* To render the template to ``stdout``:

  .. literalinclude:: template/render-exec-stdout.cmd
     :language: text
     :emphasize-lines: 1
  .. literalinclude:: template/render-exec-stdout.out
     :language: text

  Shell redirection via ``|``, ``>``, et al. may also be used to stream output to a file, another process, etc.

* To render the template to a file via command-line argument:

  .. literalinclude:: template/render-exec-file.cmd
     :language: text
     :emphasize-lines: 1

  The content of ``rendered``:

  .. literalinclude:: template/rendered
     :language: jinja

* With the ``--dry-run`` flag specified, nothing is written to ``stdout`` (or to a file if ``--output-file`` is specified), but a report of what would have been written is logged to ``stderr``:

  .. literalinclude:: template/render-exec-dry-run.cmd
     :language: text
     :emphasize-lines: 1
  .. literalinclude:: template/render-exec-dry-run.out
     :language: text

* To read the template from ``stdin`` and render to ``stdout``:

  .. literalinclude:: template/render-exec-read-stdin.cmd
     :language: text
     :emphasize-lines: 1
  .. literalinclude:: template/render-exec-read-stdin.out
     :language: text

* If the values file has an unrecognized (or no) extension, ``uw`` will not know how to parse its contents:

  .. literalinclude:: template/render-exec-bad-extension.cmd
     :language: text
     :emphasize-lines: 1
  .. literalinclude:: template/render-exec-bad-extension.out
     :language: text

  In this case, the format can be explicitly specified (``values.txt`` is identical to ``values.yaml``):

  .. literalinclude:: template/render-exec-explicit-extension.cmd
     :language: text
     :emphasize-lines: 1
  .. literalinclude:: template/render-exec-explicit-extension.out
     :language: text

* To request verbose log output:

  .. literalinclude:: template/render-exec-verbose.cmd
     :language: text
     :emphasize-lines: 1
  .. literalinclude:: template/render-exec-verbose.out
     :language: text

  Note that ``uw`` logs to ``stderr``. Use :shell-redirection:`shell redirection<>` as needed.

* The following examples use the YAML file ``greeting.yaml`` with contents:

  .. literalinclude:: template/greeting.yaml
     :language: yaml

  It is an error to render a template without providing all needed values.

  .. literalinclude:: template/render-exec-missing-value.cmd
     :language: text
     :emphasize-lines: 1
  .. literalinclude:: template/render-exec-missing-value.out
     :language: text

  Values may also be supplemented by ``key=value`` command-line arguments:

  .. literalinclude:: template/render-exec-cli-value.cmd
     :language: text
     :emphasize-lines: 1
  .. literalinclude:: template/render-exec-cli-value.out
     :language: text

  The optional ``--env`` switch allows environment variables to be used to supply values:

  .. literalinclude:: template/render-exec-env-value.cmd
     :language: text
     :emphasize-lines: 1
  .. literalinclude:: template/render-exec-env-value.out
     :language: text

  Values from ``key=value`` arguments override values from file, and environment variables override both:

  .. literalinclude:: template/render-exec-combo-value.cmd
     :language: text
     :emphasize-lines: 1
  .. literalinclude:: template/render-exec-combo-value.out
     :language: text

Note that, in the previous two examples, the ``var=val`` syntax preceding the ``uw`` command is shell syntax for exporting environment variable ``var`` only for the duration of the command that follows. It should not be confused with the two ``key=value`` pairs later on the command line, which are arguments to ``uw``.)

* Jinja2 supports references to additional templates via, for example, `import <https://jinja.palletsprojects.com/en/latest/templates/#import>`_ expressions, and ``uw`` provides support as follows:

  #. By default, the directory containing the primary template file is used as the search path for additional templates.
  #. The optional ``--search-path`` flag overrides the default search path with any number of explicitly specified, colon-separated paths.

  For example, given file ``template-with-macros``

  .. literalinclude:: template/template-with-macros
     :language: jinja

  and file ``macros`` (in the same directory as ``template-with-macros``)

  .. literalinclude:: template/macros
     :language: jinja

  the template is rendered as

  .. literalinclude:: template/render-exec-macros.cmd
     :language: text
     :emphasize-lines: 1
  .. literalinclude:: template/render-exec-macros.out
     :language: text

  The ``--search-path`` option could also be specified with a colon-separated set of directories to be searched for templates.

  **NB**: Reading the primary template from ``stdin`` requires use of ``--search-path``, as there is no implicit directory related to the input. For example, given the existence of directory ``macros-dir``:

  .. literalinclude:: template/render-exec-macros-dir.cmd
     :language: text
     :emphasize-lines: 1
  .. literalinclude:: template/render-exec-macros-dir.out
     :language: text

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
         Show version info and exit
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
