# Shared resources for workflow scripts.

CI_CONDA_DIR=/tmp/conda
CI_CONDA_SH=$CI_CONDA_DIR/etc/profile.d/conda.sh

ci_conda_activate() {
  source $CI_CONDA_SH
  conda activate
}

ci_tag() {
  echo $(jq -r .version recipe/meta.json)
}
