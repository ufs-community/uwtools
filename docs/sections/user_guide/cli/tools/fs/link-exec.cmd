rm -rf link-dst
uw fs link --target-dir link-dst --config-file link-config.yaml --key-path config.files
echo
tree link-dst
