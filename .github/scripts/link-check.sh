# Actions invokes script with: bash -e <script>

set -a

source $(dirname ${BASH_SOURCE[0]})/common.sh
ci_conda_activate
cd docs
source install-deps
make linkcheck
