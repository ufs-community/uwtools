Forecast YAML
=============

The structured YAML to run a forecast is described below. It is enforced via JSON Schema.

The ``forecast:`` section
~~~~~~~~~~~~~~~~~~~~~~~~~

The ``platform:`` section
~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: yaml

  platform:
    mpicmd: srun # required
    scheduler: slurm

The ``platform:`` section describes necessary facts about the computational platform.

``mpicmd:`` is the MPI command used to run the model executable. Typical options are ``srun``, ``mpirun``, ``mpiexec``, etc. System administrators should be able to direct an appropriate choice, if needed.

``scheduler:`` is the name of the batch system. Supported options are ``lfs``, ``pbs``, and ``slurm``.

The ``preprocessing:`` section
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: yaml

  preprocessing:
    initial_conditios:
      offset: 0 # optional, default
      output_file_template: # required
    lateral_boundary_conditions:
      interval_hours: 3 # optional, default
      offset: 0 # optional, default
      output_file_template: # required

The optional ``initial_conditions:`` section describes the location of initial conditions prepared from another forecast system (i.e., not cycled data assimilation initial conditions).

``offset:`` is the integer number of hours indicates how many hours earlier the external model used for initial conditions started compared to the desired forecast cycle

``output_file_template:`` is a string defining the path to the initial condition file prepared for the foreast.


The optional ``lateral_boundary_conditions:`` section optionally describes how the lateral boundary conditions have been prepared for a limited-area configuration of the model forecast. It is required for a limited-area forecast. The following entries in its subtree are used for the forecast:

``interval_hours:`` is the integer number of hours setting how frequently the lateral boundary conditions will be used in the model forecast

``offset:`` is the integer number of hours indicates how many hours earlier the external model used for boundary conditions started compared to the desired forecast cycle

``output_file_template:`` is a string defining the path to the lateral boundary conditions files prepared for the foreast. It accepts the integer ``forecast_hour`` as a Python template, e.g., ``/path/to/srw.t00z.gfs_bndy.tile7.f{forecast_hour:03d}.nc``



The ``user:`` section
~~~~~~~~~~~~~~~~~~~~~

.. code-block:: yaml

  user:
    account: my_account # optional

``account:`` is the user account associated with the batch system




