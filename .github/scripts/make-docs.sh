. $(dirname ${BASH_SOURCE[0]})/common.sh

build_and_check_docs() {
  set -eux
  . docs/install-deps
  make docs
  check_for_diffs "UNEXPECTED DOC UPDATES DETECTED"
}

ci_conda_activate
CONDEV_SHELL_CMD=build_and_check_docs condev-shell
