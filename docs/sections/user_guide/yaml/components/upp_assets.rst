.. _upp_assets_yaml:

upp_assets
==========

Structured YAML to configure the UPP post-processor is validated by JSON Schema and requires the ``upp_assets:`` block, described below. This driver provisions required assets for UPP under the assumption that it will be executed by another process.

.. include:: /shared/injected_cycle.rst
.. include:: /shared/injected_leadtime.rst

Here is a prototype UW YAML ``upp_assets:`` block, explained in detail below:

.. highlight:: yaml
.. literalinclude:: /shared/drivers/upp_assets.yaml

UW YAML for the ``upp_assets:`` Block
-------------------------------------

.. include:: /shared/stager.rst

namelist:
^^^^^^^^^

.. include:: /shared/upp_namelist.rst

.. include:: /shared/validate_namelist.rst

rundir:
^^^^^^^

The path to the run directory.
