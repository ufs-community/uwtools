rm -rf dst-copy-timedep
uw file copy --target-dir dst-copy-timedep --config-file copy-config-timedep.yaml --cycle 2024-05-29T12 --leadtime 6 config files
echo
tree dst-copy-timedep
