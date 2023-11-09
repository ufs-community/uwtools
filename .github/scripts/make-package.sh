# Actions invokes script with: bash -e <script>

source $(dirname ${BASH_SOURCE[0]})/common.sh
ci_conda_activate
set -x
make package
