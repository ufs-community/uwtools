rm -rf link-dst-timedep
uw file link --target-dir link-dst-timedep --config-file link-config-timedep.yaml --cycle 2024-05-29T12 --leadtime 6 config files
echo
tree link-dst-timedep
