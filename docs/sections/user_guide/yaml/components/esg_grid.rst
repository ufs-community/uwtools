.. _esg_grid_yaml:

esg_grid
========

Structured YAML to run :ufs-utils:`regional_esg_grid<regional-esg-grid>` is validated by JSON Schema and requires the ``esg_grid:`` block, described below. If ``esg_grid`` is to be run via a batch system, the ``platform:`` block, described :ref:`here <platform_yaml>`, is also required.

Here is a prototype UW YAML ``esg_grid:`` block, explained in detail below:

.. highlight:: yaml
.. literalinclude:: /shared/esg_grid.yaml

UW YAML for the ``esg_grid:`` Block
------------------------------------

execution:
^^^^^^^^^^

See :ref:`this page <execution_yaml>` for details.

namelist:
^^^^^^^^^
Supports ``base_file:`` and ``update_values:`` blocks (see the :ref:`updating_values` for details). Namelist options are described :ufs-utils:`regional_esg_grid<regional-esg-grid>`.

.. include:: /shared/validate_namelist.rst

run_dir:
^^^^^^^^

The path to the run directory.
