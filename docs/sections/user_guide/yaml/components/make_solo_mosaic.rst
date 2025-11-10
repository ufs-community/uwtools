.. _make_solo_mosaic_yaml:

make_solo_mosaic
================

Structured YAML to run the component ``make_solo_mosaic`` is validated by JSON Schema and requires the ``make_solo_mosaic:`` block, described below. If ``make_solo_mosaic`` is to be run via a batch system, the ``platform:`` block, described :ref:`here <platform_yaml>`, is also required.

Documentation for the UFS Utils ``make_solo_mosaic`` program is :ufs-utils:`here <make-solo-mosaic>`.

Here is a prototype UW YAML ``make_solo_mosaic:`` block, explained in detail below:

.. highlight:: yaml
.. literalinclude:: /shared/drivers/make_solo_mosaic.yaml

UW YAML for the ``make_solo_mosaic:`` Block
-------------------------------------------

config:
^^^^^^^

Describes the required parameters to run a ``make_solo_mosaic`` configuration.

  **dir:**

  The path to the directory that contains the tile grid files.

  **mosaic_name:**

  The optional name of the output file.

  **num_tiles:**

  Number of tiles in the mosaic.

  **periodx:**

  The period in the x-direction of the mosaic.

  **periody:**

  The period in the y-direction of the mosaic.

  **tile_file:**

  The grid file name of all of the tiles in the mosaic.

execution:
^^^^^^^^^^

See :ref:`here <execution_yaml>` for details.

rundir:
^^^^^^^

The path to the run directory.
