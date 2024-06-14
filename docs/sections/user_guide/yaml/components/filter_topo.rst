.. _filter_topo_yaml:

filter_topo
===========

Structured YAML to run the component ``filter_topo`` is validated by JSON Schema and requires the ``filter_topo:`` block, described below. If ``filter_topo`` is to be run via a batch system, the ``platform:`` block, described :ref:`here <platform_yaml>`, is also required.

Documentation for the UFS Utils ``filter_topo`` program is :ufs-utils:`here <orog-gsl>`.

Here is a prototype UW YAML ``filter_topo:`` block, explained in detail below:

.. highlight:: yaml
.. literalinclude:: /shared/filter_topo.yaml

UW YAML for the ``filter_topo:`` Block
--------------------------------------

config:
^^^^^^^

Configuration parameters for the ``orog_gsl`` component.

  **input_grid_file:**

  Path to the tiled input grid file.

namelist:
^^^^^^^^^

Supports ``base_file:`` and ``update_values:`` blocks (see :ref:`updating_values` for details). Namelist options are described :ufs-utils:`here<id48>`.

.. include:: /shared/validate_namelist.rst

execution:
^^^^^^^^^^

See :ref:`here <execution_yaml>` for details.

run_dir:
^^^^^^^^

The path to the run directory.
