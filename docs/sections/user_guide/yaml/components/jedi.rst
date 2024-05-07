.. _jedi_yaml:

jedi
====

Structured YAML to run JEDI is validated by JSON Schema and requires the ``jedi:`` block, described below. If ``jedi`` is to be run via a batch system, the ``platform:`` block, described :ref:`here <platform_yaml>`, is also required.

.. include:: ../../../../shared/injected_cycle.rst

Here is a prototype UW YAML jedi: block, explained in detail below:

.. highlight:: yaml
.. literalinclude:: ../../../../shared/jedi.yaml

UW YAML for the ``jedi:`` Block
-------------------------------

execution:
^^^^^^^^^^

See :ref:`this page <execution_yaml>` for details.

configuration_file:
^^^^^^^^^^^^^^^^^^^
Supports ``base_file:`` and ``update_values:`` blocks (see the :ref:`updating_values` for details).

files_to_copy:
^^^^^^^^^^^^^^

See :ref:`this page <files_yaml>` for details.

files_to_link:
^^^^^^^^^^^^^^

Identical to ``files_to_copy:`` except that symbolic links will be created in the run directory instead of copies.

run_dir:
^^^^^^^^

The path to the run directory.
