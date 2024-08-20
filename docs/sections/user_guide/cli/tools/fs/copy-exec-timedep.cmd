rm -rf copy-dst-timedep
uw fs copy --target-dir copy-dst-timedep --config-file copy-config-timedep.yaml --cycle 2024-05-29T12 --leadtime 6 config files
echo
tree copy-dst-timedep
