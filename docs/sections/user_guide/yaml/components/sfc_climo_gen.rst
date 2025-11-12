.. _sfc_climo_gen_yaml:

sfc_climo_gen
=============

Structured YAML to run :sfc-climo-gen:`sfc_climo_gen<>` is validated by JSON Schema and requires the ``sfc_climo_gen:`` block, described below. If ``sfc_climo_gen`` is to be run via a batch system, the ``platform:`` block, described :ref:`here <platform_yaml>`, is also required.

Here is a prototype UW YAML ``sfc_climo_gen:`` block, explained in detail below:

.. highlight:: yaml
.. literalinclude:: /shared/drivers/sfc_climo_gen.yaml

UW YAML for the ``sfc_climo_gen:`` Block
----------------------------------------

execution:
^^^^^^^^^^

See :ref:`this page <execution_yaml>` for details.

namelist:
^^^^^^^^^

Supports ``base_file:`` and ``update_values:`` blocks (see :ref:`updating_values` for details). Namelist options are described :ufs-utils:`here <id56>`.

.. include:: /shared/validate_namelist.rst

rundir:
^^^^^^^

The path to the run directory.
