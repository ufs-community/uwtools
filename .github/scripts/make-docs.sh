set -ae
. $(dirname ${BASH_SOURCE[0]})/common.sh
ci_conda_activate
cd docs
. install-deps
make docs
