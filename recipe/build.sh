set -eux
# Install Python code:
python -m pip install -vv .
# Remove pip build directory:
rm -rf build
# Copy files needed during test phase:
dst=../test_files
mkdir -pv $dst
mv -v $PKG_NAME $dst/
cp -v $RECIPE_DIR/../pyproject.toml $dst/
