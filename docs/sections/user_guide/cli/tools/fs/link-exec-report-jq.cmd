rm -rf link-dst
uw fs link --report --target-dir link-dst --config-file link-config-report.yaml 2>/dev/null | jq -r .ready[]
