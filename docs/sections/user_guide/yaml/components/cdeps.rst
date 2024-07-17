.. _cdeps_yaml:

cdeps
=====

Structured YAML to run :cdeps:`cdeps<>` is validated by JSON Schema and requires the ``cdeps:`` block, described below.

.. include:: /shared/injected_cycle.rst

Here is a prototype UW YAML ``cdeps:`` block, explained in detail below:

.. highlight:: yaml
.. literalinclude:: /shared/cdeps.yaml

UW YAML for the ``cdeps:`` Block
--------------------------------

atm_in
^^^^^^

Configures the atm namelist file. Supports ``base_file:`` and ``update_values:`` blocks (see :ref:`updating_values` for details). Namelist options are described :cdeps:`???<>`.

.. include:: /shared/validate_namelist.rst

atm_streams
^^^^^^^^^^^

Configures the atm streams.

ocn_in
^^^^^^

Configures the ocn namelist file. Supports ``base_file:`` and ``update_values:`` blocks (see :ref:`updating_values` for details). Namelist options are described :cdeps:`???<>`.

.. include:: /shared/validate_namelist.rst

atm_streams
^^^^^^^^^^^

Configures the atm streams.

rundir
^^^^^^

The path to the run directory.
