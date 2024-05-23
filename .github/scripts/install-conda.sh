set -eux
source $(dirname ${BASH_SOURCE[0]})/common.sh
url=https://github.com/conda-forge/miniforge/releases/download/23.1.0-4/Miniforge3-23.1.0-4-Linux-x86_64.sh
installer=/tmp/$(basename $url)
wget --no-verbose -O $installer $url
bash $installer -bfp $CI_CONDA_DIR
set +ux
ci_conda_activate
conda install --quiet --yes --channel maddenp --repodata-fn repodata.json anaconda-client condev
