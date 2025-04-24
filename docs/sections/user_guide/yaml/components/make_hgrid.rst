.. _make_hgrid_yaml:

make_hgrid
==========

Structured YAML to run :ufs-utils:`make_hgrid<make-hgrid>` is validated by JSON Schema and requires the ``make_hgrid:`` block, described below. If ``make_hgrid`` is to be run via a batch system, the ``platform:`` block, described :ref:`here <platform_yaml>`, is also required.

.. important::
   YAML keys and their descriptions are taken largely verbatim from the ``make_hgrid`` tool source code, available :fre-nctools:`here<make_hgrid.c>`. Best effort has been made to ensure its requirements are followed in the ``schema`` but users must ensure their parameters are valid to the source tool.

Here is a prototype UW YAML ``make_hgrid:`` block, explained in detail below:

.. highlight:: yaml
.. literalinclude:: /shared/make_hgrid.yaml

UW YAML for the ``make_hgrid:`` Block
-------------------------------------

execution:
^^^^^^^^^^

See :ref:`this page <execution_yaml>` for details.

config:
^^^^^^^

Describes the required parameters to run a ``make_hgrid`` configuration.

  **grid_type:**

  ``grid_type`` is the primary required key that defines the grid and additional required keys. It is specified with one of the following recognized key words:

  .. list-table:: Grid Types and Requirements
     :widths: 20 80
     :header-rows: 1

     * - Grid Type
       - Requirements
     * - ``beta_plane_grid``
       - For setting geometric factors according to beta plane. ``f_plane_latitude`` needs to be specified.
     * - ``conformal_cubic_grid``
       - ``nratio`` is an optional argument.
     * - ``f_plane_grid``
       - For setting geometric factors according to f-plane. ``f_plane_latitude`` must be specified.
     * - ``from_file``
       - ``my_grid_file`` must be specified.
     * - ``gnomonic_ed``
       - Equal distance gnomonic cubic grid.
     * - ``simple_cartesian_grid``
       - ``xbnds``, ``ybnds`` must be specified to define the grid bounds location and grid size. ``simple_dx`` and ``simple_dy`` must be specified to specify uniform cell length.
     * - ``spectral_grid``
       - No other optional or required arguments.
     * - ``regular_lonlat_grid``
       - ``nxbnds``, ``nybnds``, ``xbnds``, ``ybnds`` must be specified to define the grid bounds.
     * - ``tripolar_grid``
       - ``nxbnds``, ``nybnds``, ``xbnds``, ``ybnds`` must be specified to define the grid bounds.

  **angular_midpoint:**

  If specified, when ``grid_type`` is ``from_file`` and the input is a NetCDF file, then the supergrid face midpoint coordinates are simply and independently (the lat independently from the lon) calculated as simple angular midpoints from the model grid coordinates.

  **center:**

  Specify the center location of grid.

  **do_cube_transform:**

  Set to re-orient the rotated cubed sphere so that tile 6 has 'north' facing upward. When ``do_cube_transform`` is set, the following must be set: ``stretch_factor``, ``latget_lon``, and ``target_lat``.

  **do_schmidt:**

  Set to do Schmidt transformation to create a stretched grid. When ``do_schmidt`` is set, the following must be set: ``stretch_factor``, ``target_lon`` and ``target_lat``.

  **dlat:**

  Nominal resolution of meridional regions.

  **dlon:**

  Nominal resolution of zonal regions.

  **great_circle_algorithm:**

  When specified, great_circle_algorithm will be used to compute grid cell area.

  **grid_name:**

  Specify the grid name.

  **halo:**

  Halo size is to make sure the nest, including the halo region, is fully contained within a single parent (coarse) tile. It only needs to be specified when ``nest_grids`` is set.

  **lat_join:**

  Specify latitude for joining spherical and rotated bipolar grid. Default value is 65 degrees.

  **my_grid_file:**

  Read grid information from 'my_grid_file'. The file format can be ascii file or netcdf file. Required when ``grid_type`` is ``from_file``.

  **nest_grids:**

  Set to create this # nested grids as well as the global grid. This option could only be set when ``grid_type`` is ``gnomonic_ed``.

  **istart_nest:**

  Specify the list of starting i-direction index(es) of nest grid(s) in parent tile supergrid(Fortran index).

  **iend_nest:**

  Specify the list of ending i-direction index(es) of nest grids in parent tile supergrid(Fortran index).

  **jstart_nest:**

  Specify the list of starting j-direction index(es) of nest grids in parent tile supergrid(Fortran index).

  **jend_nest:**

  Specify the list of ending j-direction index(es) of nest grids in parent tile supergrid(Fortran index).

  **non_length_angle:**

  When specified, will not output length(dx,dy) and angle (angle_dx, angle_dy).

  **nlat:**

  Number of model grid points(supergrid) for each meridinal regions of varying resolution.

  **nlon:**

  Number of model grid points(supergrid) for each zonal regions of varying resolution.

  **nxbnds:**

  Specify number of zonal regions for varying resolution.

  **nybnds:**

  Specify number of meridinal regions for varying resolution.

  **nratio:**

  Specify the refinement ratio when calculating cell length and area of supergrid.

  **out_halo:**

  Extra halo size data to be written out. This is only works for ``gnomonic_ed``.

  **parent_tile:**

  Specify the list of the parent tile number(s) of nest grid(s).

  **refine_ratio:**

  Specify the list of refinement ratio(s) for nest grid(s).

  **rotate_poly:**

  Set to calculate polar polygon areas by calculating the area of a copy of the polygon, with the copy  being rotated far away from the pole.

  **shift_fac:**

  Shift west by 180/shift_fac. Default value is 18.

  **simple_dx:**

  Specify the uniform cell length in x-direction for simple cartesian grid.

  **simple_dy:**

  Specify the uniform cell length in y-direction for simple cartesian grid.

  **stretch_factor:**

  Stretching factor for the grid.

  **target_lat:**

  Center latitude of the highest resolution tile.

  **target_lon:**

  Center longitude of the highest resolution tile.

  **verbose:**

  Will print out running time message when this is set. Otherwise the run will be silent when there is no error.

  **xbnds:**

  Specify boundaries for defining zonal regions of varying resolution. When ``tripolar`` is present, also defines the longitude of the two new poles.

  **ybnds:**

  Specify boundaries for defining meridional regions of varying resolution.

rundir:
^^^^^^^

The path to the run directory.
