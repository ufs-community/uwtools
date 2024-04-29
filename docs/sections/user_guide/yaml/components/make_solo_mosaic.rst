.. _make_solo_mosaic_yaml:

make_solo_mosaic
================

Structured YAML to run the WRF preprocessing component ``make_solo_mosaic`` is validated by JSON Schema and requires the ``make_solo_mosaic:`` block, described below. If ``make_solo_mosaic`` is to be run via a batch system, the ``platform:`` block, described :ref:`here <platform_yaml>`, is also required.

Documentation for the UFS Utils ``make_solo_mosaic`` program is :ufs-utils:`here <make-solo-mosaic>`.

Here is a prototype UW YAML ``make_solo_mosaic:`` block, explained in detail below:

.. highlight:: yaml
.. literalinclude:: ../../../../shared/global_equiv_resol.yaml

UW YAML for the ``make_solo_mosaic:`` Block
-------------------------------------------

execution:
^^^^^^^^^^

See :ref:`here <execution_yaml>` for details.


run_dir:
^^^^^^^^

The path to the directory where ``make_solo_mosaic`` will find its namelist and write its outputs.
