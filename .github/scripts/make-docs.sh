. $(dirname ${BASH_SOURCE[0]})/common.sh
ci_conda_activate
. docs/install-deps
make docs
git diff # PM REMOVE
check_for_diffs "UNEXPECTED DOC UPDATES DETECTED"
