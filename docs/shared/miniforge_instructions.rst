Visit the :miniforge:`Miniforge releases page<releases/latest>` and obtain the URL and filename for the ``Miniforge3-[os]-[architecture].sh`` installer appropriate to your system, for example ``Miniforge3-Linux-x86_64.sh`` or ``Miniforge3-MacOSX-arm64.sh``. Download, install, and activate. Modify the ``$HOME/conda`` installation directory per your needs.

   .. code-block:: text

      wget <URL>
      bash <filename> -bfp $HOME/conda
      rm <filename>
      source $HOME/conda/etc/profile.d/conda.sh
      conda activate

   After initial installation, this conda may be activated at any time with the command:

   .. code-block:: text

      source $HOME/conda/etc/profile.d/conda.sh && conda activate
