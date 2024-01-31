# Actions invokes script with: bash -e <script>

set -ux
source $(dirname ${BASH_SOURCE[0]})/common.sh
tag=$(ci_tag)
if git ls-remote --tags origin | grep -q "/$tag$"; then
  (set +x && echo TAG $tag ALREADY EXISTS)
  exit 1
fi
