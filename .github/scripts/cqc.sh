. $(dirname ${BASH_SOURCE[0]})/common.sh

cqc() {
  set -eux
  notrace conda install --quiet --yes python=$PYTHON_VERSION
  pushd src
  pip install --editable . # corrects Python version in entry-point script
  popd
  make test
  uw --version
}

if [[ ! -v PYTHON_VERSION ]]; then
  notrace echo PYTHON_VERSION must be set
  false
fi

notrace ci_conda_activate
CONDEV_SHELL_CMD=cqc notrace condev-shell
