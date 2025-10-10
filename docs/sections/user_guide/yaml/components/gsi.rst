.. _gsi_yaml:

gsi
===

Structured YAML to run GSI is validated by JSON Schema and requires the ``gsi:`` block, described below. If ``gsi`` is to be run via a batch system, the ``platform:`` block, described :ref:`here <platform_yaml>`, is also required.

.. include:: /shared/injected_cycle.rst

Here is a prototype UW YAML ``gsi:`` block, explained in detail below:

.. highlight:: yaml
.. literalinclude:: /shared/gsi.yaml


UW YAML for the ``gsi:`` Block
----------------------------------

coupler.res:
^^^^^^^^^^^^


  **template_file:**

    The path to a Jinja2 template file to be rendered, using the values from the
    ``template_values:`` block for the ``coupler.res`` file.

  **template_values:**

    The key/value pairs that are required by the ``template_file``.

execution:
^^^^^^^^^^

See :ref:`this page <execution_yaml>` for details.

.. include:: /shared/stager.rst

filelist:
^^^^^^^^^

An optional list of files to be included in the ``filelist03`` text file required by GSI when
running with ``regional_ensemble_option = 1`` for global ensembles.

namelist:
^^^^^^^^^

Supports ``base_file:`` and ``update_values:`` blocks (see :ref:`updating_values` for details).

.. include:: /shared/validate_namelist.rst

obs_input_file:
^^^^^^^^^^^^^^^

Path to a file that contains only the ``OBS_INPUT::`` text block needed for the GSI namelist.

rundir:
^^^^^^^

The path to the run directory.
