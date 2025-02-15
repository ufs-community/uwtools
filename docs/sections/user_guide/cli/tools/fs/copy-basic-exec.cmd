rm -rf dst/copy
uw fs copy --target-dir dst/copy --config-file copy-basic-config.yaml --key-path config.files
echo
tree dst/copy
