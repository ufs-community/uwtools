.. _ioda_yaml:

ioda
====

Structured YAML to run IODA is validated by JSON Schema and requires the ``ioda:`` block, described below. If ``ioda`` is to be run via a batch system, the ``platform:`` block, described :ref:`here <platform_yaml>`, is also required.

.. include:: /shared/injected_cycle.rst

Here is a prototype UW YAML ``ioda:`` block, explained in detail below:

.. highlight:: yaml
.. literalinclude:: /shared/ioda.yaml

UW YAML for the ``ioda:`` Block
-------------------------------

execution:
^^^^^^^^^^

See :ref:`this page <execution_yaml>` for details.

configuration_file:
^^^^^^^^^^^^^^^^^^^

Supports ``base_file:`` and ``update_values:`` blocks (see :ref:`updating_values` for details).

.. include:: /shared/stager.rst

rundir:
^^^^^^^

The path to the run directory.
