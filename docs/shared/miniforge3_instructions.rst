.. include:: links.rst

This recipe uses the ``aarch64`` (64-bit ARM) Miniforge for Linux, and installs into ``$HOME/conda``. Adjust as necessary for your target system.

1. Download, install, and activate the latest :miniforge3:`Miniforge3<#download>` for your system. If an existing conda (:miniforge:`Miniforge<>`, :miniconda:`Miniconda<>`, :anaconda:`Anaconda<>`, etc.) installation is available and writable, you may activate that and skip this step and continue on to the next.

  .. code:: sh

    wget https://github.com/conda-forge/miniforge/releases/latest/download/Miniforge3-Linux-aarch64.sh
    bash Miniforge3-Linux-aarch64.sh -bfp ~/conda
    rm Miniforge3-Linux-aarch64.sh
    source ~/conda/etc/profile.d/conda.sh
    conda activate
