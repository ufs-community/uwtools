set -ae
source $(dirname ${BASH_SOURCE[0]})/common.sh
ci_conda_activate
set -ux
f=recipe/meta.json
glob="$(jq -r .name $f)-$(jq -r .version $f)-*_$(jq -r .buildnum $f).tar.bz2"
for x in $(find $CI_CONDA_DIR/conda-bld -type f -name "$glob"); do
  anaconda -t $ANACONDA_TOKEN upload $x
done
# Refresh Anaconda badges on GitHub.
ids=(
  6c9ed105fbe1d674e82460d5e7fa6c7eb8e2eb6eb3640c763a8189f407e2a9a2/68747470733a2f2f616e61636f6e64612e6f72672f7566732d636f6d6d756e6974792f7577746f6f6c732f6261646765732f76657273696f6e2e737667
  a6f1f3ab481647dc492ab577cb7e60522efded549caf0544ba863d0a72958179/68747470733a2f2f616e61636f6e64612e6f72672f7566732d636f6d6d756e6974792f7577746f6f6c732f6261646765732f6c61746573745f72656c656173655f646174652e737667
)
for id in ${ids[*]}; do
  curl -s -X PURGE https://camo.githubusercontent.com/$id | jq .
done
