rm -rf dst-link-timedep
uw file link --target-dir dst-link-timedep --config-file link-config-timedep.yaml --cycle 2024-05-29T12 --leadtime 6 config files
echo
tree dst-link-timedep
