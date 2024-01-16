This recipe uses the ``aarch64`` (64-bit ARM) Miniforge for Linux, and installs into ``$HOME/conda``. Adjust as necessary for the target system.

#. Download, install, and activate the latest :miniforge3:`Miniforge<>` for the target system.

   .. code-block:: text

      wget https://github.com/conda-forge/miniforge/releases/latest/download/Miniforge3-Linux-aarch64.sh
      bash Miniforge3-Linux-aarch64.sh -bfp ~/conda
      rm Miniforge3-Linux-aarch64.sh
      source ~/conda/etc/profile.d/conda.sh
      conda activate

   After initial installation, this conda may be activated with the command

   .. code-block:: text

      source ~/conda/etc/profile.d/conda.sh && conda activate
