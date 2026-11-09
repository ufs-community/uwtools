set -aeux

CI_CONDA_DIR=/tmp/conda
CI_CONDA_SH=$CI_CONDA_DIR/etc/profile.d/conda.sh

check_for_diffs() {
  test -z "$(git status --porcelain)" && return 0
  git --no-pager diff
  notrace echo $1
  return 1
}

ci_conda_activate() {
  notrace . $CI_CONDA_SH
  notrace conda activate
}

notrace() {
  set +x
  $@
  set -x
}
