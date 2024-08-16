.. _upp_yaml:

upp
===

Structured YAML to run the UPP post-processor is validated by JSON Schema and requires the ``upp:`` block, described below. If UPP is to be run via a batch system, the ``platform:`` block, described :ref:`here <platform_yaml>`, is also required.

.. include:: ../../../../shared/injected_cycle.rst
.. include:: ../../../../shared/injected_leadtime.rst

Here is a prototype UW YAML ``upp:`` block, explained in detail below:

.. highlight:: yaml
.. literalinclude:: ../../../../shared/upp.yaml

UW YAML for the ``upp:`` Block
------------------------------

execution:
^^^^^^^^^^

See :ref:`this page <execution_yaml>` for details.

files_to_copy:
^^^^^^^^^^^^^^

See :ref:`this page <files_yaml>` for details.

files_to_link:
^^^^^^^^^^^^^^

Identical to ``files_to_copy:`` except that symbolic links will be created in the run directory instead of copies.

namelist:
^^^^^^^^^

Supports ``base_file:`` and ``update_values:`` blocks (see the :ref:`updating_values` for details).

The following namelists and variables can be customized:

.. list-table::
   :widths: 10 95
   :header-rows: 1

   * - Namelist
     - Variables
   * - ``model_inputs``
     - ``datestr``, ``filename``, ``filenameflat``, ``filenameflux``, ``grib``, ``ioform``, ``modelname``, ``submodelname``
   * - ``nampgb``
     - ``aqf_on``, ``d2d_chem``, ``d3d_on``, ``filenameaer``, ``gccpp_on``, ``gocart_on``, ``gtg_on``, ``hyb_sigp``, ``kpo``, ``kpv``, ``kth``, ``method_blsn``, ``nasa_on``, ``numx``, ``po``, ``popascal``, ``pv``, ``rdaod``, ``slrutah_on``, ``th``, ``vtimeunits``, ``write_ifi_debug_files``

Read more on the UPP namelists, including variable meanings and appropriate values, `here <https://upp.readthedocs.io/en/develop/BuildingRunningTesting/InputsOutputs.html#itag>`_.

.. include:: ../../../../shared/validate_namelist.rst

run_dir:
^^^^^^^^

The path to the run directory.
