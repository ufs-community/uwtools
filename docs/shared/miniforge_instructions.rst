Visit the :miniforge:`releases page<releases/latest>` and obtain the URL and filename for the ``Miniforge3-[os]-[architecture].sh`` installer appropriate to your system, for example ``Miniforge3-Linux-x86_64.sh`` or ``Miniforge3-MacOSX-arm64.sh``.

#. Download, install, and activate the latest :miniforge:`Miniforge<>` for the target system.

   .. code-block:: text

      wget <URL>
      bash <filename> -bfp ~/conda
      rm <filename>
      source ~/conda/etc/profile.d/conda.sh
      conda activate

   After initial installation, this conda may be activated with the command:

   .. code-block:: text

      source ~/conda/etc/profile.d/conda.sh && conda activate
