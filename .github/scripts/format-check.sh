# Actions invokes script with: bash -e <script>

set -a

unformatted() {
  set -x
  make format
  if [[ -n "$(git status --porcelain)" ]]; then
    (set +x && echo UNFORMATTED CODE DETECTED)
    return 1
  fi
  return 0
}

source $(dirname ${BASH_SOURCE[0]})/common.sh
source $CI_CONDA_SH
conda activate
CONDEV_SHELL_CMD=unformatted condev-shell
