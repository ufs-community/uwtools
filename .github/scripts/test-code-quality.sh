. $(dirname ${BASH_SOURCE[0]})/common.sh

run_tests() {
  set -eux
  env=python-$PYTHON_VERSION
  devpkgs=$(jq .packages.dev[] recipe/meta.json | tr -d ' "')
  conda create --yes --name $env --quiet $devpkgs
  set +x
  conda activate $env
  conda install --yes python=$PYTHON_VERSION
  . notebooks/install-deps
  set -x
  git clean -dfx
  pip install --editable src # sets new Python version in entry-point scripts
  make test && make notebooks && make test-nb
  status=$?
  set +x
  conda deactivate
  set -x
  return $status
}

SUPPORTED_PYTHON_VERSIONS=( 3.11 3.12 3.13 3.14 3.15 )

ci_conda_activate
for version in ${SUPPORTED_PYTHON_VERSIONS[*]}; do
  PYTHON_VERSION=$version
  CONDEV_SHELL_CMD=run_tests condev-shell
done
