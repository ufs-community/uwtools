``ecflow``
==========

.. contents::
   :backlinks: top
   :depth: 1
   :local:

The ``uw`` mode for realizing and validating ecFlow suite definitions.

.. literalinclude:: ecflow/help.cmd
   :language: text
   :emphasize-lines: 1
.. literalinclude:: ecflow/help.out
   :language: text

.. _cli_ecflow_realize_examples:

``realize``
-----------

In ``uw`` terminology, to ``realize`` a configuration file is to transform it from its raw form into its final, usable state. In the case of ``uw ecflow``, that means transforming a structured UW YAML file into an ecFlow Suite Definition file and corresponding ecf script files. The structured YAML language required by UW closely follows the syntax defined by ecFlow.

.. literalinclude:: ecflow/realize-help.cmd
   :language: text
   :emphasize-lines: 1
.. literalinclude:: ecflow/realize-help.out
   :language: text

Examples
^^^^^^^^

The examples in this section use a UW YAML file ``ecflow.yaml`` with contents:

.. literalinclude:: ecflow/ecflow.yaml
   :language: yaml

* To realize a UW YAML input file to ``stdout`` in ecFlow Suite Definition format:

  .. literalinclude:: ecflow/realize-stdout.cmd
     :language: text
     :emphasize-lines: 1
  .. literalinclude:: ecflow/realize-stdout.out
     :language: text

* To realize a UW YAML input file and write the Suite Definition and ecf scripts to a directory:

  .. literalinclude:: ecflow/realize-file.cmd
     :language: text
     :emphasize-lines: 1
  .. literalinclude:: ecflow/realize-file.out
     :language: text

  This creates a ``suite.def`` file and a hierarchy of ``.ecf`` script files in the ``workflow_output/`` directory.

.. _cli_ecflow_validate_examples:

``validate``
------------

The ``validate`` action validates a UW YAML ecFlow configuration against the internal JSON Schema.

.. literalinclude:: ecflow/validate-help.cmd
   :language: text
   :emphasize-lines: 1
.. literalinclude:: ecflow/validate-help.out
   :language: text

Examples
^^^^^^^^

* To validate an ecFlow config file:

  .. literalinclude:: ecflow/validate-good.cmd
     :language: text
     :emphasize-lines: 1
  .. literalinclude:: ecflow/validate-good.out
     :language: text

  The ecFlow execution configuration accepts either ``executable`` (the standard UW format) or ``jobcmd`` (an ecFlow-specific format). Both are valid and will pass schema validation. When both are provided, ``jobcmd`` takes precedence.
