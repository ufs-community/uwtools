``make_hgrid``
==============

The ``uw`` mode for configuring and running the UFS Utils preprocessing component ``make_hgrid``. Documentation for this UFS Utils component is :ufs-utils:`here <make-hgrid>`.

.. literalinclude:: make_hgrid/help.cmd
   :language: text
   :emphasize-lines: 1
.. literalinclude:: make_hgrid/help.out
   :language: text

All tasks take the same arguments. For example:

.. literalinclude:: make_hgrid/run-help.cmd
   :language: text
   :emphasize-lines: 1
.. literalinclude:: make_hgrid/run-help.out
   :language: text

Examples
^^^^^^^^

The examples use a configuration file named ``config.yaml`` with content similar to:

.. highlight:: yaml
.. literalinclude:: ../../../../shared/make_hgrid.yaml

Its contents are described in section :ref:`make_hgrid_yaml`.

* Run ``make_hgrid`` on an interactive node

  .. code-block:: text

     $ uw make_hgrid run --config-file config.yaml

  The driver creates a ``runscript.make_hgrid`` file in the directory specified by ``run_dir:`` in the config and runs it, executing ``make_hgrid``.

* Run ``make_hgrid`` via a batch job

  .. code-block:: text

     $ uw make_hgrid run --config-file config.yaml --batch

  The driver creates a ``runscript.make_hgrid`` file in the directory specified by ``run_dir:`` in the config and submits it to the batch system. Running with ``--batch`` requires a correctly configured ``platform:`` block in ``config.yaml``, as well as appropriate settings in the ``execution:`` block under ``make_hgrid:``.

  Looking at the run command in ``runscript.make_hgrid`` shows us the specified executable as well as the YAML keys converted to appropriate command line flags.

  .. code-block:: text

     time make_hgrid --grid_type gnomonic_ed --do_schmidt --great_circle_algorithm --grid_name C96_foo --halo 1 --nest_grids 1 --istart_nest 10 --iend_nest 87 --jstart_nest 19 --jend_nest 78 --nlon 192 --parent_tile 6 --refine_ratio 2 --stretch_factor 1.0001 --target_lon -97.5 --target_lat 38.5

* Specifying the ``--dry-run`` flag results in the driver logging messages about actions it would have taken, without actually taking any.

  .. code-block:: text

     $ uw make_hgrid run --config-file config.yaml --batch --dry-run
