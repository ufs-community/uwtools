set -ae
source $(dirname ${BASH_SOURCE[0]})/common.sh
ci_conda_activate
set -x
make package
