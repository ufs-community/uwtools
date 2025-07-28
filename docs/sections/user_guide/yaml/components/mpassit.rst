.. _mpassit_yaml:

mpassit
=======

Structured YAML to run MPASSIT is validated by JSON Schema and requires the ``mpassit:`` block, described below. If ``mpassit`` is to be run via a batch system, the ``platform:`` block, described :ref:`here <platform_yaml>`, is also required.

.. include:: /shared/injected_cycle.rst

Here is a prototype UW YAML ``mpassit:`` block, explained in detail below:

.. highlight:: yaml
.. literalinclude:: /shared/mpassit.yaml


UW YAML for the ``mpassit:`` Block
----------------------------------

execution:
^^^^^^^^^^

See :ref:`this page <execution_yaml>` for details.

files_to_copy:
^^^^^^^^^^^^^^

See :ref:`this page <files_yaml>` for details.

To reduce duplication of information in this section, it may be helpful to template the file that depends on the number of cores being used to run the executable. For example, instead of:

.. code-block:: text

   mpassit:
     files_to_copy:
       x1.999.graph.info.part.192: /path/to/x1.999.graph.info.part.192

Jinja2 expressions can be used to reference the number of cores used in execution:

.. code-block:: text

   mpassit:
     files_to_copy:
       x1.999.graph.info.part.{{ mpassit.execution.batchargs.cores }}: /path/to/x1.999.graph.info.part.{{ mpassit.execution.batchargs.cores }}

files_to_link:
^^^^^^^^^^^^^^

Identical to ``files_to_copy:`` except that symbolic links will be created in the run directory instead of copies.

namelist:
^^^^^^^^^

Supports ``base_file:`` and ``update_values:`` blocks (see :ref:`updating_values` for details).

.. include:: /shared/validate_namelist.rst

rundir:
^^^^^^^

The path to the run directory.
