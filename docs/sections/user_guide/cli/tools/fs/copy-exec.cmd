rm -rf copy-dst
uw fs copy --target-dir copy-dst --config-file copy-config.yaml --key-path config.files
echo
tree copy-dst
