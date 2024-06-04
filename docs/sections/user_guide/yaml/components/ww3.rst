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

.. important:: The WaveWatchIII namelist file is provisioned by rendering an input template file containing Jinja2 expressions. Unlike namelist files provisioned by ``uwtools`` for other components, the WaveWatchIII namelist file will not be validated.

  **template_file:**

  The path to the base ``ww3_shel.nml`` file that comes from the WW3 build.

  **template_values:**

  Key-value pairs necessary to render all Jinja2 expressions in the input template file named by ``template_file:``.

run_dir:
^^^^^^^^

The path to the run directory.
