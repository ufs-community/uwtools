``ecflow``
=========

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

In ``uw`` terminology, to ``realize`` a configuration file is to transform it from its raw form into its final, usable state. In the case of ``uw ecflow``, that means transforming a structured UW YAML file into an :ecflow:`ecFlow<>` suite definition file (``suite.def``) and, optionally, a set of ecf scripts. The structured YAML language required by UW closely follows the concepts defined by ecFlow.

See :ref:`ecflow_workflows` for more information about the structured UW YAML for ecFlow.

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

* To realize a UW YAML input file to ``stdout`` in ecFlow suite definition format:

  .. literalinclude:: ecflow/realize-exec-stdout.cmd
     :language: text
     :emphasize-lines: 1
  .. literalinclude:: ecflow/realize-exec-stdout.out
     :language: text

* To realize a UW YAML input file to a directory (writes ``suite.def`` inside that directory):

  .. literalinclude:: ecflow/realize-exec-dir.cmd
     :language: text
     :emphasize-lines: 2
  .. literalinclude:: ecflow/realize-exec-dir.out
     :language: text

* To read the UW YAML from ``stdin`` and write the suite definition to ``stdout``:

  .. literalinclude:: ecflow/realize-exec-stdin-stdout.cmd
     :language: text
     :emphasize-lines: 1
  .. literalinclude:: ecflow/realize-exec-stdin-stdout.out
     :language: text

* To also generate ecf scripts in a ``scripts/`` directory:

  .. literalinclude:: ecflow/realize-exec-scripts.cmd
     :language: text
     :emphasize-lines: 1
  .. literalinclude:: ecflow/realize-exec-scripts.out
     :language: text

  The ``--scripts-path`` option specifies the directory under which ecf scripts are written. Each script is placed at ``<scripts-path>/<suite>/<family_path>/<scriptname>.ecf``. For the example above, the generated scripts would be:

  * ``scripts/forecast/prep/obs.ecf`` (for ``task_get_obs`` under ``family_prep``)
  * ``scripts/forecast/model.ecf`` (for ``task_run_model`` directly under the suite)

  .. note::

     The ecf script name is derived from the portion of the task name after the first underscore. For example, ``task_get_obs`` produces the script ``obs.ecf``, and ``task_run_model`` produces ``model.ecf``.

.. _cli_ecflow_validate_examples:

``validate``
------------

.. literalinclude:: ecflow/validate-help.cmd
   :language: text
   :emphasize-lines: 1
.. literalinclude:: ecflow/validate-help.out
   :language: text

Examples
^^^^^^^^

The examples in this section use the UW YAML file ``ecflow.yaml`` shown above.

* To validate a UW YAML config file:

  .. literalinclude:: ecflow/validate-good-file.cmd
     :language: text
     :emphasize-lines: 1
  .. literalinclude:: ecflow/validate-good-file.out
     :language: text

* To validate a UW YAML config from ``stdin``:

  .. literalinclude:: ecflow/validate-good-stdin.cmd
     :language: text
     :emphasize-lines: 1
  .. literalinclude:: ecflow/validate-good-stdin.out
     :language: text

* When the config is invalid:

  In this example, the top-level ``ecflow:`` key is missing.

  .. literalinclude:: ecflow/validate-bad-file.cmd
     :language: text
     :emphasize-lines: 1
  .. literalinclude:: ecflow/validate-bad-file.out
     :language: text
