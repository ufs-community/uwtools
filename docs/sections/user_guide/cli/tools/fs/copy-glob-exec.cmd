rm -rf dst/copy-glob
uw fs copy --report --target-dir dst/copy-glob --config-file copy-glob-config.yaml
echo
tree dst/copy-glob
