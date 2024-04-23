.. _global_equiv_resol_yaml:

global_equiv_resol_yaml
=======================

Structured YAML to run the WRF preprocessing component ``global_equiv_resol_yaml`` is validated by JSON Schema and requires the ``global_equiv_resol_yaml:`` block, described below. If ``global_equiv_resol_yaml`` is to be run via a batch system, the ``platform:`` block, described :ref:`here <platform_yaml>`, is also required.

Here is a prototype UW YAML ``global_equiv_resol_yaml:`` block, explained in detail below:

.. highlight:: yaml
.. literalinclude:: ../../../../shared/global_equiv_resol_yaml.yaml

UW YAML for the ``global_equiv_resol_yaml:`` Block
--------------------------------------------------

execution:
^^^^^^^^^^

See :ref:`here <execution_yaml>` for details.

input_grid_file:
^^^^^^^^^^^^^^^^

The path to the input grid file required by the program.

run_dir:
^^^^^^^^

The path to the directory where ``global_equiv_resol`` will find its namelist and write its outputs.
