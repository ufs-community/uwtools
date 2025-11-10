.. _enkf_yaml:

enkf
====

Structured YAML to run EnKF is validated by JSON Schema and requires the ``enkf:`` block, described below. If ``enkf`` is to be run via a batch system, the ``platform:`` block, described :ref:`here <platform_yaml>`, is also required.

.. include:: /shared/injected_cycle.rst

Here is a prototype UW YAML ``enkf:`` block, explained in detail below:

.. highlight:: yaml
.. literalinclude:: /shared/drivers/enkf.yaml


UW YAML for the ``enkf:`` Block
-------------------------------

background_files:
^^^^^^^^^^^^^^^^^

  **ensemble_size:**

    The integer size of the expected ensemble.

  **files:**

    A :ref:`File Block <files_yaml>` describing the background ensemble files. The `member` variable
    will be made available to Jinja2 expressions used in this block.

execution:
^^^^^^^^^^

See :ref:`this page <execution_yaml>` for details.

.. include:: /shared/stager.rst

namelist:
^^^^^^^^^

Supports ``base_file:`` and ``update_values:`` blocks (see :ref:`updating_values` for details).

.. include:: /shared/validate_namelist.rst

rundir:
^^^^^^^

The path to the run directory.
