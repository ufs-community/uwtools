.. _upp_assets_yaml:

upp_assets
==========

Structured YAML to configure the UPP post-processor is validated by JSON Schema and requires the ``upp_assets:`` block, described below. This driver provisions required assets for UPP under the assumption that it will be executed by another process.

.. include:: /shared/injected_cycle.rst
.. include:: /shared/injected_leadtime.rst

Here is a prototype UW YAML ``upp_assets:`` block, explained in detail below:

.. highlight:: yaml
.. literalinclude:: /shared/upp_assets.yaml

UW YAML for the ``upp_assets:`` Block
-------------------------------------

files_to_copy:
^^^^^^^^^^^^^^

See :ref:`this page <files_yaml>` for details.

files_to_link:
^^^^^^^^^^^^^^

Identical to ``files_to_copy:`` except that symbolic links will be created in the run directory instead of copies.

namelist:
^^^^^^^^^

.. include:: /shared/upp_namelist.rst

.. include:: /shared/validate_namelist.rst

rundir:
^^^^^^^

The path to the run directory.
