.. _global_equiv_resol_yaml:

global_equiv_resol
==================

Structured YAML to run the component ``global_equiv_resol`` is validated by JSON Schema and requires the ``global_equiv_resol:`` block, described below. If ``global_equiv_resol`` is to be run via a batch system, the ``platform:`` block, described :ref:`here <platform_yaml>`, is also required.

Documentation for the UFS Utils ``global_equiv_resol`` program is :ufs-utils:`here <global-equiv-resol>`.

Here is a prototype UW YAML ``global_equiv_resol:`` block, explained in detail below:

.. highlight:: yaml
.. literalinclude:: /shared/drivers/global_equiv_resol.yaml

UW YAML for the ``global_equiv_resol:`` Block
---------------------------------------------

execution:
^^^^^^^^^^

See :ref:`this page <execution_yaml>` for details.

input_grid_file:
^^^^^^^^^^^^^^^^

The path to the input grid file required by the program.

rundir:
^^^^^^^

The path to the run directory.
