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

.. important:: Fortran namelists for WaveWatchIII are used here as templates to be realized. Input namelists will not have their configurations validated, only the associated YAML. Other files are not currently supported.

  **template_file:**

  The path to the base ``ww3_shel.nml`` file that comes from the WW3 build.

  **template_values:**

  The set of key-value pairs that will render the appropriate XML entries in the template input file.

run_dir:
^^^^^^^^

The path to the run directory.
