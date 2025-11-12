. $(dirname ${BASH_SOURCE[0]})/common.sh
ci_conda_activate
cd docs
. install-deps
make docs
check_for_diffs "UNEXPECTED DOC UPDATES DETECTED"
