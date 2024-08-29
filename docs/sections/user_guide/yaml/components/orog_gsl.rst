.. _orog_gsl_yaml:

orog_gsl
========

Structured YAML to run the component ``orog_gsl`` is validated by JSON Schema and requires the ``orog_gsl:`` block, described below. If ``orog_gsl`` is to be run via a batch system, the ``platform:`` block, described :ref:`here <platform_yaml>`, is also required.

Documentation for the UFS Utils ``orog_gsl`` program is :ufs-utils:`here <orog-gsl>`.

Here is a prototype UW YAML ``orog_gsl:`` block, explained in detail below:

.. highlight:: yaml
.. literalinclude:: /shared/orog_gsl.yaml

UW YAML for the ``orog_gsl:`` Block
-----------------------------------

config:
^^^^^^^

Configuration parameters for the ``orog_gsl`` component.

  **halo:**

  Halo number (-439 for no halo).

  **input_grid_file:**

  Path to the tiled input grid file.

  **resolution:**

  Input grid resolution index.

  **tile:**

  Tile number (1-6 for global, 7 for regional).

  **topo_data_2p5m:**

  Path to file containing global topographic data on 2.5-minute lat-lon grid.

  **topo_data_30s:**

  Path to file containing global topographic data on 30-second lat-lon grid.

execution:
^^^^^^^^^^

See :ref:`here <execution_yaml>` for details.

rundir:
^^^^^^^

The path to the run directory.
