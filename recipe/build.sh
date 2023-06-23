set -eux
# Copy tool config to support test run during packaging:
cp -v $(realpath $RECIPE_DIR/../pyproject.toml) .
# Install Python code:
python -m pip install . -vv
