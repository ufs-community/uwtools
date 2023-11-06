# Actions invokes script with: bash -e <script>

source /tmp/conda/etc/profile.d/conda.sh
conda activate
set -x
make package
