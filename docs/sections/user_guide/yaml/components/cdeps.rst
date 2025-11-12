.. _cdeps_yaml:

cdeps
=====

Structured YAML to run :cdeps:`CDEPS<index.html>` is validated by JSON Schema and requires the ``cdeps:`` block, described below.

.. include:: /shared/injected_cycle.rst

Here is a prototype UW YAML ``cdeps:`` block, explained in detail below:

.. highlight:: yaml
.. literalinclude:: /shared/drivers/cdeps.yaml

UW YAML for the ``cdeps:`` Block
--------------------------------

atm_in
^^^^^^

Configures the atm namelist file. Supports ``base_file:`` and ``update_values:`` blocks (see :ref:`updating_values` for details). Namelist options are described :cdeps:`here<streams.html>`.

.. include:: /shared/validate_namelist.rst

atm_streams
^^^^^^^^^^^

Configures the atm streams.

  **streams:**

  The ``streams:`` block may contain sub-blocks ``stream01`` through ``stream09``. Each such sub-block specifies a stream configuration to be used to render the Jinja2 template file named by ``template_file:`` (see below). Supported keys and values are described :cdeps:`here<streams.html>`.

  **template_file:**

  The path to a Jinja2 template file to be rendered, using the values from the ``streams:`` block (see above), to a streams file.

ocn_in
^^^^^^

Configures the ocn namelist file. Supports ``base_file:`` and ``update_values:`` blocks (see :ref:`updating_values` for details). Namelist options are described :cdeps:`here<streams.html>`.

.. include:: /shared/validate_namelist.rst

ocn_streams
^^^^^^^^^^^

Configures the ocn streams. See the ``atm_streams:`` block, above, which is configured identically.

rundir
^^^^^^

The path to the run directory.
