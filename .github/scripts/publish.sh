# -*- mode: sh -*-

# Actions invokes script with: bash -e <script>

source /tmp/conda/etc/profile.d/conda.sh
conda activate
set -ux
f=recipe/meta.json
glob="$(jq -r .name $f)-$(jq -r .version $f)-*_$(jq -r .buildnum $f).tar.bz2"
for x in $(find conda/conda-bld -type f -name "$glob"); do
  anaconda -t $ANACONDA_TOKEN upload $x
done
