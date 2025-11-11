# Shared resources for workflow scripts.

CI_CONDA_DIR=/tmp/conda
CI_CONDA_SH=$CI_CONDA_DIR/etc/profile.d/conda.sh

check_for_diffs() {
  local msg=$1
  if [[ -n "$(git status --porcelain)" ]]; then
    git --no-pager diff
    (set +x && echo $msg)
    return 1
  fi
  return 0
}

ci_conda_activate() {
  . $CI_CONDA_SH
  conda activate
}
