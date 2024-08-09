Installation
============

.. note::

   Developers should visit the :doc:`Developer Setup <../contributor_guide/developer_setup>` section located in the :doc:`Contributor Guide <../contributor_guide/index>`.

The recommended installation mechanism uses the Python package and virtual-environment manager :conda:`conda<>`. The :miniforge:`Miniforge<>` variant of :miniconda:`Miniconda<>`, which by default uses packages from the :conda-forge:`conda-forge<>` project, is an especially useful basis for working with conda.

Use an Existing conda Installation
----------------------------------

Install Into an Existing Environment
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

To install ``uwtools`` into an existing environment in an existing conda (e.g., :miniforge:`Miniforge<>`, :miniconda:`Miniconda<>`, :anaconda:`Anaconda<>`) installation:

#. Activate that environment.
#. Identify the ``uwtools`` version number to install from the available versions shown by ``conda search -c ufs-community --override-channels uwtools``.
#. Install ``uwtools`` into the active environment:

   .. code-block:: text

      conda install -c ufs-community -c conda-forge --override-channels uwtools=<version>

Create a Standalone ``uwtools`` Environment
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

To create a standalone conda environment providing ``uwtools``:

#. Identify the ``uwtools`` version number to install from the available versions shown by ``conda search -c ufs-community --override-channels uwtools``.
#. Create the environment (here named ``uwtools`` via the ``-n`` flag, but any name may be used):

   .. code-block:: text

      conda create -n uwtools -c ufs-community -c conda-forge --override-channels uwtools=<version>

Use a Fresh Miniforge Installation
----------------------------------

#. .. include:: /shared/miniforge_instructions.rst

#. Continue with the `Use an Existing conda Installation`_ instructions.

Build the ``uwtools`` Package Locally
-------------------------------------

#. Install the necessary build packages. If your conda's ``base`` environment is not writable (e.g. you are using a shared conda installation), first create and activate your own environment, or follow the `Use a Fresh Miniforge Installation`_ instructions.

   .. code-block:: text

      conda install -y -c conda-forge --override-channels conda-build conda-verify

#. In a clone of the :uwtools:`uwtools repository<>`, build the ``uwtools`` package:

   .. code-block:: text

      cd /to/your/uwtools/clone
      make package

#. Verify local availability of the newly built package:

   .. code-block:: text

      conda search -c $CONDA_PREFIX/conda-bld --override-channels uwtools

#. Optionally, create an environment from the newly built package (specify the version if multiple local packages are available):

   .. code-block:: text

      conda create -y -n uwtools -c $CONDA_PREFIX/conda-bld -c conda-forge --override-channels uwtools[=<version>]
