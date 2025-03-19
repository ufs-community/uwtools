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

The examples in this section use a template file ``template`` with contents:

.. literalinclude:: template/template
   :language: jinja

and a YAML file called ``values.yaml`` with contents:

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

  Shell redirection may also be used to stream output to a file, another process, etc.

* To render the template to a file via command-line argument:

  .. literalinclude:: template/render-exec-file.cmd
     :language: text
     :emphasize-lines: 2
  .. literalinclude:: template/render-exec-file.out
     :language: text

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

  The format must be explicitly specified (here, ``values.txt`` is identical to ``values.yaml``):

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

  Note that ``uw`` logs to ``stderr``. Use shell redirection as needed.

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

  The ``--search-path`` option can also be specified with a colon-separated set of directories to be searched for templates.

  **NB**: Reading the primary template from ``stdin`` requires use of ``--search-path``, as there is no implicit directory related to the input. For example, given the existence of directory ``macros-dir``:

  .. literalinclude:: template/render-exec-macros-dir.cmd
     :language: text
     :emphasize-lines: 1
  .. literalinclude:: template/render-exec-macros-dir.out
     :language: text

* Non-YAML-formatted files may also be used as value sources. For example, ``values.sh`` with contents

  .. literalinclude:: template/values.sh
     :language: fortran

  can be used to render ``template``:

  .. literalinclude:: template/render-exec-sh.cmd
     :language: text
     :emphasize-lines: 1
  .. literalinclude:: template/render-exec-sh.out
     :language: text

.. _cli_template_translate_examples:

``translate``
-------------

.. literalinclude:: template/translate-help.cmd
   :language: text
   :emphasize-lines: 1
.. literalinclude:: template/translate-help.out
   :language: text

Examples
^^^^^^^^

The examples in this section use atparse-formatted template file ``atparse.txt`` with contents:

  .. literalinclude:: template/atparse.txt
     :language: text

* To convert an atparse-formatted template file to Jinja2 format:

  .. literalinclude:: template/translate-exec-stdout.cmd
     :language: text
     :emphasize-lines: 1
  .. literalinclude:: template/translate-exec-stdout.out
     :language: text

  Shell redirection may also be used to stream output to a file, another process, etc.

* To convert the template to a file via command-line argument:

  .. literalinclude:: template/translate-exec-file.cmd
     :language: text
     :emphasize-lines: 2
  .. literalinclude:: template/translate-exec-file.out
     :language: text

* With the ``--dry-run`` flag specified, nothing is written to ``stdout`` (or to a file if ``--output-file`` is specified), but a report of what would have been written is logged to ``stderr``:

  .. literalinclude:: template/translate-exec-dry-run.cmd
     :language: text
     :emphasize-lines: 1
  .. literalinclude:: template/translate-exec-dry-run.out
     :language: text
