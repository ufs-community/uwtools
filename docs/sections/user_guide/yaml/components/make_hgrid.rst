.. _make_hgrid_yaml:

make_hgrid
==========

Structured YAML to run :ufs-utils:`make_hgrid<make-hgrid>` is validated by JSON Schema and requires the ``make_hgrid:`` block, described below. If ``make_hgrid`` is to be run via a batch system, the ``platform:`` block, described :ref:`here <platform_yaml>`, is also required.

Here is a prototype UW YAML ``make_hgrid:`` block, explained in detail below:

.. highlight:: yaml
.. literalinclude:: ../../../../shared/make_hgrid.yaml

UW YAML for the ``make_hgrid:`` Block
-------------------------------------

execution:
^^^^^^^^^^

See :ref:`here <execution_yaml>` for details.

run_dir:
^^^^^^^^

The path to the directory where ``make_hgrid`` will write its outputs.

config:
^^^^^^^

Describes the required parameters to run a ``make_hgrid`` configuration. 


grid_type:
""""""""""

Specify grid type with one of the following recognized key words:

* from_file:              --my_grid_file must be specified.
* spectral_grid:          no other optional or required arguments.
* regular_lonlat_grid:    --nxbnds, --nybnds --xbnds, --ybnds, must be specified to define the grid bounds.
* tripolar_grid:          --nxbnds, --nybnds, --xbnds, --ybnds, must be specified to define the grid bounds.
* conformal_cubic_grid:   --nratio is optional argument.
* gnomonic_ed:            equal distance gnomonic cubic grid.
* simple_cartesian_grid:  --xbnds, --ybnds must be specified to define the grid bounds location and grid size. --simple_dx and --simple_dy must be specified to specify uniform cell length.
* f_plane_grid:           For setting geometric fractors according f-plane. f_plane_latitude must be specified
* beta_plane_grid:        For setting geometric fractors according to beta plane. f_plane_latitude need to be specified 


my_grid_file:
"""""""""""""

When this flag is present, the program will read grid information from 'my_grid_file'. The file format can be ascii file or netcdf file.


nxbnds:
"""""""

Specify number of zonal regions for varying resolution.


nybnds:
"""""""

Specify number of meridinal regions for varying resolution.


xbnds:
""""""

Specify boundaries for defining zonal regions of varying resolution. When --tripolar is present, also defines the longitude of the two new poles.


ybnds:
""""""

Specify boundaries for defining meridional regions of varying resolution.


nlon:
"""""

Number of model grid points(supergrid) for each zonal regions of varying resolution.

nlat:
"""""

Number of model grid points(supergrid) for each meridinal regions of varying resolution.

dlon:
"""""

Nominal resolution of zonal regions.

dlat:
"""""

Nominal resolution of meridional regions.

lat_join:
"""""""""

Specify latitude for joining spherical and rotated bipolar grid. Default value is 65 degree

nratio:
"""""""

Specify the refinement ratio when calculating cell length and area of supergrid.

simple_dx:
""""""""""

Specify the uniform cell length in x-direction for simple cartesian grid.

simple_dy:
""""""""""

Specify the uniform cell length in y-direction for simple cartesian grid.

grid_name:
""""""""""

Specify the grid name.

center:
"""""""

Specify the center location of grid.

shift_fac:
""""""""""

Shift west by 180/shift_fac. Default value is 18.

do_schmidt:
"""""""""""

Set to do Schmidt transformation to create astretched grid. When do_schmidt is set, the following must be set: --stretch_factor, --target_lon and --target_lat.

do_cube_transform:
""""""""""""""""""

Set to re-orient the rotated cubed sphere so that tile 6 has 'north' facing upward. When do_cube_transform is set, the following must be set: --stretch_factor, --latget_lon, and --target_lat.  

stretch_factor:
"""""""""""""""

Stretching factor for the grid.

target_lon:
"""""""""""

Center longitude of the highest resolution tile.

target_lat:
"""""""""""

Center latitude of the highest resolution tile.

nest_grids:
"""""""""""

Set to create this # nested grids as well as the global grid.

parent_tile:
""""""""""""

Specify the list of the parent tile number(s) of nest grid(s).

refine_ratio:
"""""""""""""

Specify the list of refinement ratio(s) for nest grid(s).

halo:
"""""

Halo size is to make sure the nest, including the halo region, is fully contained within a single parent (coarse) tile.

istart_nest:
""""""""""""

Specify the list of starting i-direction index(es) of nest grid(s) in parent tile supergrid(Fortran index).

iend_nest:
""""""""""

Specify the list of ending i-direction index(es) of nest grids in parent tile supergrid(Fortran index).

jstart_nest:
""""""""""""

Specify the list of starting j-direction index(es) of nest grids in parent tile supergrid(Fortran index). 

jend_nest:
""""""""""

Specify the list of ending j-direction index(es) of nest grids in parent tile supergrid(Fortran index).

great_circle_algorithm:
"""""""""""""""""""""""

When specified, great_circle_algorithm will be used to compute grid cell area. 

out_halo:
"""""""""

Extra halo size data to be written out.

angular_midpoint:
"""""""""""""""""

If specified, when grid_type is from_file and the input is a NetCDF file, then the supergrid face midpoint coordinates are simply and independely (the lat independently from the lon) calculated as simple angular midpoints from the model grid coordiantes.

non_length_angle:
"""""""""""""""""

When specified, will not output length(dx,dy) and angle (angle_dx, angle_dy).

rotate_poly:
""""""""""""

Set to calculate polar polygon areas by calculating the area of a copy of the polygon, with the copy  being rotated far away from the pole.

verbose:
""""""""

Will print out running time message when this is set. Otherwise the run will be silent when there is no error.

Example UW YAML With SRW YAML References
----------------------------------------

The UW YAML for ``make_hgrid`` uses keys from the ``UFS_UTILS`` tool parameters. Keys used in other apps such as SRW can be converted to direct parameters, with SRW used as an example here:

.. code-block:: yaml

   make_hgrid:
      config:
         grid_type: "gnomonic_ed"
         nlon: ${2*GFDLgrid_NUM_CELLS}
         grid_name: ${GRID_GEN_METHOD}
         do_schmidt: True
         stretch_factor: ${GFDLgrid_STRETCH_FAC}
         target_lon: ${GFDLgrid_LON_T6_CTR}
         target_lat: ${GFDLgrid_LAT_T6_CTR}
         nest_grid: True
         parent_tile: 6
         refine_ratio: ${GFDLgrid_REFINE_RATIO}
         istart_nest: ${GFDLgrid_ISTART_OF_RGNL_DOM_WITH_WIDE_HALO_ON_T6SG}
         jstart_nest: ${GFDLgrid_JSTART_OF_RGNL_DOM_WITH_WIDE_HALO_ON_T6SG}
         iend_nest: ${GFDLgrid_IEND_OF_RGNL_DOM_WITH_WIDE_HALO_ON_T6SG}
         jend_nest: ${GFDLgrid_JEND_OF_RGNL_DOM_WITH_WIDE_HALO_ON_T6SG}
         halo: 1
         great_circle_algorithm: True