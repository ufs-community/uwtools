.. _ungrib_yaml:

ungrib
=============

Structured YAML to run :sfc-climo-gen:`ungrib<>` is validated by JSON Schema and requires the ``ungrib:`` block, described below. If ``ungrib`` is to be run via a batch system, the ``platform:`` block, described :ref:`here <platform_yaml>`, is also required.

Here is a prototype UW YAML ``ungrib:`` block, explained in detail below:

.. highlight:: yaml
.. literalinclude:: ../../../../shared/ungrib.yaml


UW YAML for the ``ungrib:`` Block
----------------------------------------

execution:
^^^^^^^^^^

See :ref:`here <execution_yaml>` for details.


gfs_file:
^^^^^^^^

The path to the GRIB-formatted file to be processed by ``ungrib``.


run_dir:
^^^^^^^^

The path to the directory where ``ungrib`` will find its namelist and write its outputs.


vtable:
^^^^^^^^

The path to the correct variable table for the file to be processed by ``ungrib``.