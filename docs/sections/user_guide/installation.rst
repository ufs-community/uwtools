Installation
============

-  If you are a **developer**, please visit the :doc:`Developer Setup <../contributor_guide/developer_setup>` section located in the :doc:`Contributor Guide <../contributor_guide/index>`.

The recommended installation mechanism uses the Python package and virtual-environment manager :conda:`conda<>`. Specifically, these instructions detail the use of the minimal :miniforge:`Miniforge<>` variant of :miniconda:`Miniconda<>`, built to use, by default, packages from the :conda-forge:`conda-forge<>` project.

Users of the original Miniconda (or the :anaconda:`Anaconda distribution<>`) may need to add the flags ``-c conda-forge --override-channels`` to ``conda build``, ``conda create``, and ``conda install`` commands to specify the use of conda-forge packages.

Using a fresh Miniforge installation
====================================

.. include:: ../../shared/miniforge3_instructions.rst

2. Install the ``conda-build`` and ``conda-verify`` packages into the base environment. If ``conda-build`` and ``conda-verify`` are already installed in your installation’s base environment, you may skip this step.

  .. code:: sh

    conda install -y conda-build conda-verify

3. In a clone of the :uwtools:`workflow-tools repository<>`, build and install the ``uwtools`` package.

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

Note that the ``uwtools`` package’s actual name will contain version and build information, e.g. ``uwtools-0.1.0-py_0``. The ``conda create`` command will find and use the most recent :semver:`Semantic Versioning<>`-compliant package name given the base name ``uwtools``. It could also be explicitly specified as ``uwtools=0.1.0=py_0``.
