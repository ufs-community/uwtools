.. _schism_yaml:

schism
======

Structured YAML to configure :schism:`SCHISM<>` as part of a compiled coupled executable is validated by JSON Schema and requires the ``schism:`` block, described below.

Here is a prototype UW YAML ``schism:`` block, explained in detail below:

.. highlight:: yaml
.. literalinclude:: /shared/schism.yaml

UW YAML for the ``schism:`` Block
---------------------------------

namelist:
^^^^^^^^^

  .. important:: The SCHISM namelist file is provisioned by rendering an input template file containing Jinja2 expressions. Unlike namelist files provisioned by ``uwtools`` for other components, the SCHISM namelist file will not be validated.

  **template_file:**

  The path to the input template file containing Jinja2 expressions (perhaps named ``param.nml.IN``), based on the ``param.nml`` file from the SCHISM build.

  **template_values:**

  Key-value pairs necessary to render all Jinja2 expressions in the input template file named by ``template_file:``.

rundir:
^^^^^^^

The path to the run directory.
