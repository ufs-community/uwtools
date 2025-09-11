.. _upp_yaml:

upp
===

Structured YAML to run the UPP post-processor is validated by JSON Schema and requires the ``upp:`` block, described below. If UPP is to be run via a batch system, the ``platform:`` block, described :ref:`here <platform_yaml>`, is also required.

.. include:: /shared/injected_cycle.rst
.. include:: /shared/injected_leadtime.rst

Here is a prototype UW YAML ``upp:`` block, explained in detail below:

.. highlight:: yaml
.. literalinclude:: /shared/upp.yaml

UW YAML for the ``upp:`` Block
------------------------------

execution:
^^^^^^^^^^

See :ref:`this page <execution_yaml>` for details.

.. include:: /shared/stager.rst

namelist:
^^^^^^^^^

.. include:: /shared/upp_namelist.rst

.. include:: /shared/validate_namelist.rst

rundir:
^^^^^^^

The path to the run directory.
