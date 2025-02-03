d=makedirs-parent-report-jq
rm -rf $d
mkdir -p $d/subdir
chmod 550 $d/subdir # read-only
uw fs makedirs --report --target-dir $d --config-file makedirs-config-report.yaml 2>/dev/null | jq -r .ready[]
chmod 750 $d/subdir # read-write
