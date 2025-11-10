.. _chgres_cube_yaml:

chgres_cube
===========

Structured YAML to run :ufs-utils:`chgres_cube<chgres-cube>` is validated by JSON Schema and requires the ``chgres_cube:`` block, described below. If ``chgres_cube`` is to be run via a batch system, the ``platform:`` block, described :ref:`here <platform_yaml>`, is also required.

.. include:: /shared/injected_cycle.rst

Here is a prototype UW YAML ``chgres_cube:`` block, explained in detail below:

.. highlight:: yaml
.. literalinclude:: /shared/drivers/chgres_cube.yaml

UW YAML for the ``chgres_cube:`` Block
--------------------------------------

execution
^^^^^^^^^

See :ref:`this page <execution_yaml>` for details.

namelist
^^^^^^^^

Supports ``base_file:`` and ``update_values:`` blocks (see :ref:`updating_values` for details). Namelist options are described :ufs-utils:`here<global-chgres-cube-namelist-options>`.

.. include:: /shared/validate_namelist.rst

rundir
^^^^^^

The path to the run directory.
