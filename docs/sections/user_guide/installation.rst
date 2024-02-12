Installation
============

.. note::

   Developers should visit the :doc:`Developer Setup <../contributor_guide/developer_setup>` section located in the :doc:`Contributor Guide <../contributor_guide/index>`.

The recommended installation mechanism uses the Python package and virtual-environment manager :conda:`conda<>`. Specifically, these instructions assume use of the :miniforge:`Miniforge<>` variant of :miniconda:`Miniconda<>`, built to use, by default, packages from the :conda-forge:`conda-forge<>` project. Users of the original :miniconda:`Miniconda<>` or the :anaconda:`Anaconda distribution<>` should add the flags ``-c conda-forge --override-channels`` to ``conda`` commands to specify the required package channels.

Use an Existing conda Installation
----------------------------------

Install Into an Existing Environment
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

To install ``uwtools`` into an existing environment in an existing conda (e.g., :miniforge:`Miniforge<>`, :miniconda:`Miniconda<>`, :anaconda:`Anaconda<>`) installation:

#. Activate that environment.
#. Identify the ``uwtools`` version number to install from the available versions shown by ``conda search -c ufs-community --override-channels uwtools``.
#. Install ``uwtools`` into the active environment:

   .. code-block:: text

      conda install -c ufs-community uwtools=<version>

Create a Standalone ``uwtools`` Environment
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

To create a standalone conda environment providing ``uwtools``:

#. Identify the ``uwtools`` version number to install from the available versions shown by ``conda search -c ufs-community --override-channels uwtools``.
#. Create the environment (here named ``uwtools`` via the ``-n`` flag, but any name may be used):

   .. code-block:: text

      conda create -n uwtools -c ufs-community uwtools=<version>

Use a Fresh Miniforge Installation
----------------------------------

If no existing conda installation is available, install :miniforge:`Miniforge<>`.

.. include:: ../../shared/miniforge3_instructions.rst

#. Continue with the `Use an Existing conda Installation`_ instructions.

Build the ``uwtools`` Package Locally
-------------------------------------

#. Install the necessary build packages into the conda installation's base environment (see the `Use a Fresh Miniforge Installation`_ instructions if an installation is unavailable or not writable):

   .. code-block:: text

      conda install conda-build conda-verify

#. In a clone of the :uwtools:`uwtools repository<>`, build the ``uwtools`` package:

   .. code-block:: text

      cd /to/your/uwtools/clone
      conda build recipe

#. Verify local availability of the newly built package:

   .. code-block:: text

      conda search -c local --override-channels uwtools  # do not add -c conda-forge to this command

#. Optionally, create an environment from the newly built package:

   .. code-block:: text

      conda create -n uwtools -c local uwtools[=<version>]  # specify version if multiple choices are available
