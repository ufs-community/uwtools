rm -rf makedirs-parent-timedep
uw fs makedirs --target-dir makedirs-parent-timedep --config-file makedirs-timedep-config.yaml --cycle 2024-05-29T12 --leadtime 6 --key-path config
echo
tree -F makedirs-parent-timedep
