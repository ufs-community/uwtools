.. _ww3_yaml:

ww3
===

Structured YAML to configure WaveWatchIII as part of a compiled coupled executable is validated by JSON Schema and requires the ``ww3:`` block, described below.

Here is a prototype UW YAML ``ww3:`` block, explained in detail below:

.. highlight:: yaml
.. literalinclude:: ../../../../shared/ww3.yaml

UW YAML for the ``ww3:`` Block
------------------------------

namelist:
^^^^^^^^^

The WaveWatchIII namelist file can be provisioned either by:
1. Providing a path to a complete, ready-to-use namelist file as the value of the `base_file:` key and omitting the `update_values:` key, or
2. Providing a path to a namelist file containing Jinja2 expressions as the value of the `base_file:` key and a mapping from variable names to values used to render those Jinja2 expressions as the value of the `update_values:` key.

.. include:: ../../../../shared/validate_namelist.rst

run_dir:
^^^^^^^^

The path to the run directory.
