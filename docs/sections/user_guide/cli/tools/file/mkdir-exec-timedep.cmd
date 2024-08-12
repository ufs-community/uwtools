rm -rf mkdir-parent-timedep
uw file link --target-dir mkdir-parent-timedep --config-file mkdir-config-timedep.yaml --cycle 2024-05-29T12 --leadtime 6 config mkdir
echo
tree -F mkdir-parent-timedep
