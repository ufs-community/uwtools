# Actions invokes script with: bash -e <script>

set -ux
cd /tmp
url=https://github.com/conda-forge/miniforge/releases/download/23.1.0-4/Miniforge3-23.1.0-4-Linux-aarch64.sh
wget --no-verbose $url
bash $(basename $url) -bfp conda
set +ux
source conda/etc/profile.d/conda.sh
conda activate
conda install -q -y -c maddenp --repodata-fn repodata.json anaconda-client condev
