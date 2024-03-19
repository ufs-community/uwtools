.. _chgres_cube_yaml:

chgres_cube
===========

Structured YAML to run :ufs-utils:`chgres_cube<chgres-cube>` is validated by JSON Schema and requires the ``chgres_cube:`` block, described below. If ``chgres_cube`` is to be run via a batch system, the ``platform:`` block, described :ref:`here <platform_yaml>`, is also required.

Here is a prototype UW YAML ``chgres_cube:`` block, explained in detail below:

.. highlight:: yaml
.. literalinclude:: ../../../../shared/chgres_cube.yaml


UW YAML for the ``chgres_cube:`` Block
--------------------------------------

execution
^^^^^^^^^

See :ref:`here <execution_yaml>` for details.


namelist
^^^^^^^^

Supports ``base_file:`` and ``update_values:`` blocks (see the :ref:`updating_values` for details). Namelist options are described :ufs-utils:`here<global-chgres-cube-namelist-options>`.

run_dir
^^^^^^^

The path to the directory where ``chgres_cube`` will find its namelist and write its outputs.
