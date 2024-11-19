set -ae
source $(dirname ${BASH_SOURCE[0]})/common.sh
ci_conda_activate
cd docs
source install-deps
make docs
