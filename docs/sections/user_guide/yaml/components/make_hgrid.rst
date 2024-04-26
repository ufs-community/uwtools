.. _make_hgrid_yaml:

make_hgrid
========

Structured YAML to run :ufs-utils:`make_hgrid<make-hgrid>` is validated by JSON Schema and requires the ``make_hgrid:`` block, described below. If ``make_hgrid`` is to be run via a batch system, the ``platform:`` block, described :ref:`here <platform_yaml>`, is also required.

Here is a prototype UW YAML ``make_hgrid:`` block, explained in detail below:

.. highlight:: yaml
.. literalinclude:: ../../../../shared/make_hgrid.yaml

UW YAML for the ``make_hgrid:`` Block
------------------------------------

execution:
^^^^^^^^^^

See :ref:`here <execution_yaml>` for details.

run_dir:
^^^^^^^^

The path to the directory where ``make_hgrid`` will write its outputs.