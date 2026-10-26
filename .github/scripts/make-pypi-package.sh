. $(dirname ${BASH_SOURCE[0]})/common.sh
ci_conda_activate
unset CONDEV_SHELL
export PYPI_PROJECT_NAME=unified-workflow-tools
python -m build --no-isolation --wheel src
