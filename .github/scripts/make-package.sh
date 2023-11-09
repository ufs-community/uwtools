# Actions invokes script with: bash -e <script>

source $(dirname ${BASH_SOURCE[0]})/common.sh
source $CI_CONDA_SH
conda activate
set -x
make package
