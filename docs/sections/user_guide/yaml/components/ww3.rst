.. _ww3_yaml:

ww3
===

Structured YAML when including WaveWatchIII as part of a compiled coupled executable is validated by JSON Schema and requires the ``ww3:`` block, described below.

Here is a prototype UW YAML ``ww3:`` block, explained in detail below:

.. highlight:: yaml
.. literalinclude:: ../../../../shared/ww3.yaml

UW YAML for the ``ww3:`` Block
------------------------------

namelist:
^^^^^^^^^

Supports ``base_file:`` and ``update_values:`` blocks (see the :ref:`updating_values` for details).

run_dir:
^^^^^^^^

The path to the run directory.
