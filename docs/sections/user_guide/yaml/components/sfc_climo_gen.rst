.. _sfc_climo_gen_yaml:

sfc_climo_gen
=============

Structured YAML to run :sfc-climo-gen:`sfc_climo_gen<>` is validated by JSON Schema and requires the ``sfc_climo_gen:`` block, described below. If ``sfc_climo_gen`` is to be run via a batch system, the ``platform:`` block, described :ref:`here <platform_yaml>`, is also required.

Here is a prototype UW YAML ``sfc_climo_gen:`` block, explained in detail below:

.. highlight:: yaml
.. literalinclude:: ../../../../shared/sfc_climo_gen.yaml


UW YAML for the ``sfc_climo_gen:`` Block
----------------------------------------

execution:
^^^^^^^^^^

See :ref:`here <execution_yaml>` for details.


namelist:
^^^^^^^^^

Supports ``base_file:`` and ``update_values:`` blocks (see the :ref:`updating_values` for details). Namelist options are described `here <https://noaa-emcufs-utils.readthedocs.io/en/latest/ufs_utils.html#id57>`_.

run_dir:
^^^^^^^^

The path to the directory where ``sfc_climo_gen`` will find its namelist and write its outputs.