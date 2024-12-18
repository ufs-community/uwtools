# Shared resources for workflow scripts.

CI_CONDA_DIR=/tmp/conda
CI_CONDA_SH=$CI_CONDA_DIR/etc/profile.d/conda.sh

ci_conda_activate() {
  . $CI_CONDA_SH
  conda activate
}
