rm -rf makedirs-parent-timedep
uw fs makedirs --target-dir makedirs-parent-timedep --config-file makedirs-config-timedep.yaml --cycle 2024-05-29T12 --leadtime 6 config
echo
tree -F makedirs-parent-timedep
