set -ae

LATEST_UWTOOLS_VERSION= conda search -c ufs-community --override-channels uwtools | tail -n 1 | grep -Po '[0-9]+\.[0-9]+\.[0-9]'

source $(dirname ${BASH_SOURCE[0]})/common.sh
ci_conda_activate
conda install -c ufs-community -c conda-forge --override-channels --repodata-fn repodata.json uwtools=$LATEST_UWTOOLS_VERSION
cd notebooks
source install-deps
make test-nb
