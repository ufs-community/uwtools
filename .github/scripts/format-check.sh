set -ae

unformatted() {
  set -x
  make format
  if [[ -n "$(git status --porcelain)" ]]; then
    git --no-pager diff
    (set +x && echo UNFORMATTED CODE DETECTED)
    return 1
  fi
  return 0
}

. $(dirname ${BASH_SOURCE[0]})/common.sh
ci_conda_activate
CONDEV_SHELL_CMD=unformatted condev-shell
