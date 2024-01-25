# Actions invokes script with: bash -e <script>

set -ux
f=recipe/meta.json
tag=v$(jq -r .version $f)-$(jq -r .buildnum $f)
git tag $tag
git push --tags
