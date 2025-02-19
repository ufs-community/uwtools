set -ae
source $(dirname ${BASH_SOURCE[0]})/common.sh
ci_conda_activate
set -ux
f=recipe/meta.json
glob="$(jq -r .name $f)-$(jq -r .version $f)-*_$(jq -r .buildnum $f).conda"
for x in $(find $CI_CONDA_DIR/conda-bld -type f -name "$glob"); do
  anaconda -t $ANACONDA_TOKEN upload $x
done
