set -ae

SUPPORTED_PYTHON_VERSIONS=( 3.9 3.10 3.11 3.12 )

run_tests() {
  echo TESTING PYTHON $PYTHON_VERSION
  env=python-$PYTHON_VERSION
  conda create --yes --name $env --quiet python=$PYTHON_VERSION
  conda activate $env
  set -x
  python --version
  git clean -dfx
  pip install --editable src # sets new Python version in entry-point scripts
  make test
  status=$?
  conda deactivate
  return $status
}

source $(dirname ${BASH_SOURCE[0]})/common.sh
ci_conda_activate
for version in ${SUPPORTED_PYTHON_VERSIONS[*]}; do
  PYTHON_VERSION=$version
  CONDEV_SHELL_CMD=run_tests condev-shell
done
