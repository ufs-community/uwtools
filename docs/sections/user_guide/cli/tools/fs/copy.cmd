rm -rf dst/copy
uw fs copy --target-dir dst/copy --config-file copy.yaml --key-path config.files
echo
tree dst/copy
