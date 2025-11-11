. $(dirname ${BASH_SOURCE[0]})/common.sh

unformatted() {
  set -x
  make format
  check_for_diffs "UNFORMATTED CODE DETECTED"
}

ci_conda_activate
CONDEV_SHELL_CMD=unformatted condev-shell
