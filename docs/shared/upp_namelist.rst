Supports ``base_file:`` and ``update_values:`` blocks (see :ref:`updating_values` for details).

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
