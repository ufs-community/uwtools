# Actions invokes script with: bash -e <script>

set -ux
source $(dirname ${BASH_SOURCE[0]})/common.sh
installer=/tmp/$(basename $url)
wget --no-verbose -O $installer $url
bash $installer -bfp $CONDADIR
set +ux
source $CONDADIR/etc/profile.d/conda.sh
conda activate
conda install --quiet --yes --channel maddenp --repodata-fn repodata.json anaconda-client condev
