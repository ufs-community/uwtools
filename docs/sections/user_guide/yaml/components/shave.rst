.. _shave_yaml:

shave
=====

Structured YAML to run :ufs-utils:`shave<shave>` is validated by JSON Schema and requires the ``shave:`` block, described below. If ``shave`` is to be run via a batch system, the ``platform:`` block, described :ref:`here <platform_yaml>`, is also required.

Here is a prototype UW YAML ``shave:`` block, explained in detail below:

.. highlight:: yaml
.. literalinclude:: /shared/shave.yaml

UW YAML for the ``shave:`` Block
--------------------------------

execution:
^^^^^^^^^^

See :ref:`this page <execution_yaml>` for details.

config:
^^^^^^^

Describes the required parameters to run a ``shave`` configuration.

  **input_grid_file:**

  Name of the grid file with extra points to be shaved.

  **nhalo:**

  The number of halo rows/columns.

  **nx:**

  The i/x dimensions of the compute domain (not including halo).

  **ny:**

  The j/y dimensions of the compute domain (not including halo)

  **output_grid_file:**

  The path to the output file.

rundir:
^^^^^^^

The path to the run directory.
