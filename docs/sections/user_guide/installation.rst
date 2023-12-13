.. include:: links.rst

************
Installation
************

-  If you are a **developer**, please visit the `Developer Setup <../contributor_guide/developer_setup.html>`_ section located in the `Contributor Guide <../contributor_guide/index.html>`_.

The recommended installation mechanism uses the Python package and virtual-environment manager `conda`_. Specifically, these instructions detail the use of the minimal `Miniforge`_ variant of `Miniconda`_, built to use, by default, packages from the `conda-forge`_ project.

Users of the original Miniconda (or the `Anaconda`_ distribution) may need to add the flags ``-c conda-forge --override-channels`` to ``conda build``, ``conda create``, and ``conda install`` commands to specify the use of conda-forge packages.

Using a fresh Miniforge installation
====================================

.. include:: ../miniforge3_instructions.rst

2. Install the ``conda-build`` and ``conda-verify`` packages into the base environment. If ``conda-build`` and ``conda-verify`` are already installed in the your installation’s base environment, you may skip this step.

   .. code:: sh

     conda install -y conda-build conda-verify

3. In a clone of the `workflow-tools repository`_, build and install the ``uwtools`` package.

   .. code:: sh

     cd /to/your/workflow-tools/clone
     conda build recipe
     conda create -y -n uwtools -c local uwtools

4. Activate the ``uwtools`` environment.

   .. code:: sh

     conda activate uwtools

In future shells, you can activate and use this environment with:

   .. code:: sh

     source ~/conda/etc/profile.d/conda.sh
     conda activate uwtools

Note that the ``uwtools`` package’s actual name will contain version and build information, e.g. ``uwtools-0.1.0-py_0``. The ``conda create`` command will find and use the most recent `semantic versioning`_ - compliant package name given the base name ``uwtools``. It could also be explicitly specified as ``uwtools=0.1.0=py_0``.
