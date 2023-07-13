set -eux
# Install Python code:
python -m pip install -vv .
# Copy files needed during test phase:
dst=../test_files
rm -fr $dst
mkdir -pv $dst
mv -v $PKG_NAME $dst/
cp -v $SRC_DIR/pyproject.toml $dst/
