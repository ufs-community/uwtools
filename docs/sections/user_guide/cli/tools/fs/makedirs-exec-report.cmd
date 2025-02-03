d=makedirs-parent-report
rm -rf $d
mkdir -p $d/subdir
chmod 550 $d/subdir # read-only
uw fs makedirs --report --target-dir $d --config-file makedirs-config-report.yaml
chmod 750 $d/subdir # read-write
