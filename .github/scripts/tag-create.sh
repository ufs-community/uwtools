# Actions invokes script with: bash -e <script>

set -ux
source $(dirname ${BASH_SOURCE[0]})/common.sh
tag=$(ci_tag)
git tag $tag
git push --tags
