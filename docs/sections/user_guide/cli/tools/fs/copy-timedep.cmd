rm -rf dst/copy-timedep
uw fs copy --target-dir dst/copy-timedep --config-file copy-timedep.yaml --cycle 2024-05-29T12 --leadtime 6 --key-path config.files
echo
tree dst/copy-timedep
