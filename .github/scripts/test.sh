# Actions invokes script with: bash -e <script>

set -a

SUPPORTED_PYTHON_VERSIONS=( 3.9 3.10 3.11 )

run_tests() {
  echo TESTING PYTHON $PYTHON_VERSION
  set -x
  conda install -y python=$PYTHON_VERSION
  make test
}

source /tmp/conda/etc/profile.d/conda.sh
conda activate
for version in ${SUPPORTED_PYTHON_VERSIONS[*]}; do
  PYTHON_VERSION=$version
  CONDEV_SHELL_CMD=run_tests
  condev-shell
done
