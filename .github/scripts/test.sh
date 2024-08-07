set -ae

SUPPORTED_PYTHON_VERSIONS=( 3.9 3.10 3.11 3.12 )

run_tests() {
  echo TESTING PYTHON $PYTHON_VERSION
  conda install --quiet --yes --repodata-fn repodata.json python=$PYTHON_VERSION
  set -x
  pip install --editable src # set new Python version in entry-point scripts
  python --version
  git clean -dfx
  make test
  return $?
}

source $(dirname ${BASH_SOURCE[0]})/common.sh
ci_conda_activate
for version in ${SUPPORTED_PYTHON_VERSIONS[*]}; do
  PYTHON_VERSION=$version
  CONDEV_SHELL_CMD=run_tests condev-shell
done
