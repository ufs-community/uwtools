# Actions invokes script with: bash -e <script>

source $(dirname ${BASH_SOURCE[0]})/common.sh
source $CONDADIR/etc/profile.d/conda.sh
conda activate
set -x
make package
