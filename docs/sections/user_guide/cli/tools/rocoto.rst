``rocoto``
==========

.. contents::
   :backlinks: top
   :depth: 1
   :local:

The ``uw`` mode for realizing and validating Rocoto XML documents.

.. literalinclude:: rocoto/help.cmd
   :language: text
   :emphasize-lines: 1
.. literalinclude:: rocoto/help.out
   :language: text

.. _cli_rocoto_iterate_examples:

``iterate``
-----------

.. literalinclude:: rocoto/iterate-help.cmd
   :language: text
   :emphasize-lines: 1
.. literalinclude:: rocoto/iterate-help.out
   :language: text

Examples
^^^^^^^^

.. note:: Use of ``uw rocoto iterate`` requires presence of the ``rocotorun`` and ``rocotostat`` executables on ``PATH``. On HPCs, this is typically achieved by loading a system module providing Rocoto.

The following examples make use of this simple UW YAML for Rocoto config:

.. literalinclude:: rocoto/foobar.yaml
   :language: yaml

It could be rendered to a Rocoto XML document like this:

.. literalinclude:: rocoto/foobar-realize.cmd
   :language: text
   :emphasize-lines: 1
.. literalinclude:: rocoto/foobar-realize.out
   :language: xml

* To iterate only task ``foo``, which has no dependencies:

  .. literalinclude:: rocoto/iterate-foo.txt
     :language: text
     :emphasize-lines: 6
  .. literalinclude:: rocoto/iterate-foo.out
     :language: text

  Note that the second invocation of ``uw rocoto iterate`` immediately shows task ``foo`` in its final state, without iterating the workflow.

* To iterate task ``bar``, which depends on task ``foo``, iterating every 3 seconds:

  .. literalinclude:: rocoto/iterate-bar.txt
     :language: text
     :emphasize-lines: 4
  .. literalinclude:: rocoto/iterate-bar.out
     :language: text

  Note that the second invocation of ``uw rocoto iterate`` immediately shows task ``bar`` in its final state, without iterating the workflow.

.. _cli_rocoto_realize_examples:

``realize``
-----------

In ``uw`` terminology, to ``realize`` a configuration file is to transform it from its raw form into its final, usable state. In the case of ``uw rocoto``, that means transforming a structured UW YAML file into a :rocoto:`Rocoto XML<>` file. The structured YAML language required by UW closely follows the XML language defined by Rocoto.

See :ref:`rocoto_workflows` for more information about the structured UW YAML for Rocoto.

.. literalinclude:: rocoto/realize-help.cmd
   :language: text
   :emphasize-lines: 1
.. literalinclude:: rocoto/realize-help.out
   :language: text

Examples
^^^^^^^^

The examples in this section use a UW YAML file ``rocoto.yaml`` with contents:

.. literalinclude:: rocoto/rocoto.yaml
   :language: yaml

* To realize a UW YAML input file to ``stdout`` in Rocoto XML format:

  .. literalinclude:: rocoto/realize-exec-stdout.cmd
     :language: text
     :emphasize-lines: 1
  .. literalinclude:: rocoto/realize-exec-stdout.out
     :language: xml

* To realize a UW YAML input file to a file named ``rocoto.xml``:

  .. literalinclude:: rocoto/realize-exec-file.cmd
     :language: text
     :emphasize-lines: 2
  .. literalinclude:: rocoto/realize-exec-file.out
     :language: text

* To read the UW YAML from ``stdin`` and write the XML to ``stdout``:

  .. literalinclude:: rocoto/realize-exec-stdin-stdout.cmd
     :language: text
     :emphasize-lines: 1
  .. literalinclude:: rocoto/realize-exec-stdin-stdout.out
     :language: xml

* To see verbose log output (Rocoto XML and some output elided for brevity):

  .. literalinclude:: rocoto/realize-exec-stdout-verbose.cmd
     :language: text
     :emphasize-lines: 2
  .. literalinclude:: rocoto/realize-exec-stdout-verbose.out
     :language: xml

.. _cli_rocoto_validate_examples:

``validate``
------------

.. literalinclude:: rocoto/validate-help.cmd
   :language: text
   :emphasize-lines: 1
.. literalinclude:: rocoto/validate-help.out
   :language: text

Examples
^^^^^^^^

The examples in this section use a Rocoto XML file ``rocoto-good.xml`` with contents:

.. literalinclude:: rocoto/rocoto-good.xml
   :language: xml

* To validate XML from ``stdin``:

  .. literalinclude:: rocoto/validate-good-stdin.cmd
     :language: text
     :emphasize-lines: 1
  .. literalinclude:: rocoto/validate-good-stdin.out
     :language: text

* To validate XML from file ``rocoto-good.xml``:

  .. literalinclude:: rocoto/validate-good-file.cmd
     :language: text
     :emphasize-lines: 1
  .. literalinclude:: rocoto/validate-good-file.out
     :language: text

* When the XML is invalid:

  In this example, the ``<command>`` line was removed from ``rocoto-good.xml`` to create ``rocoto-bad.xml``.

  .. literalinclude:: rocoto/validate-bad-file.cmd
     :language: text
     :emphasize-lines: 1
  .. literalinclude:: rocoto/validate-bad-file.out
     :language: text

  To decode the three ``ERROR:RELAXNGV`` messages, it is easiest to read from the bottom up. They say:

  * At line 9 column 0 (i.e. ``<string>:9:0``), the element (i.e. ``<task>``) failed to validate.
  * The sequence of interleaved elements under ``<task>`` was invalid.
  * A ``<command>`` element was expected, but it wasn't found.
