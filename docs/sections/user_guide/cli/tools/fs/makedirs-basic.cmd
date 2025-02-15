rm -rf makedirs-parent
uw fs makedirs --target-dir makedirs-parent --config-file makedirs-basic.yaml --key-path config
echo
tree -F makedirs-parent
