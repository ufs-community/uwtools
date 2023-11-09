# Actions invokes script with: bash -e <script>

set -a

SUPPORTED_PYTHON_VERSIONS=( 3.11 3.10 3.9 )

run_tests() {
  echo TESTING PYTHON $PYTHON_VERSION
  conda install -qy python=$PYTHON_VERSION
  set -x
  make test
  return $?
}

source /tmp/conda/etc/profile.d/conda.sh
conda activate
CONDEV_SHELL_CMD=true condev-shell
for version in ${SUPPORTED_PYTHON_VERSIONS[*]}; do
  PYTHON_VERSION=$version
  CONDEV_SHELL_CMD=run_tests condev-shell
done
