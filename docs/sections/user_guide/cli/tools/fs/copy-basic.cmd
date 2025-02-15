rm -rf dst/copy
uw fs copy --target-dir dst/copy --config-file copy-basic.yaml --key-path config.files
echo
tree dst/copy
