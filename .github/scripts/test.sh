# Actions invokes script with: bash -e <script>

set -a

SUPPORTED_PYTHON_VERSIONS=( 3.11 3.10 3.9 )

run_tests() {
  echo TESTING PYTHON $PYTHON_VERSION
  conda install --quiet --yes python=$PYTHON_VERSION
  set -x
  pip install --editable src
  python --version
  make test
  return $?
}

source $(dirname ${BASH_SOURCE[0]})/common.sh
source $CONDADIR/etc/profile.d/conda.sh
conda activate
for version in ${SUPPORTED_PYTHON_VERSIONS[*]}; do
  PYTHON_VERSION=$version
  CONDEV_SHELL_CMD=run_tests condev-shell
done
