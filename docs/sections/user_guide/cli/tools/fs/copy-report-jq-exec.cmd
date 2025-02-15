rm -rf copy-dst
uw fs copy --report --target-dir copy-dst --config-file copy-config-report.yaml 2>/dev/null | jq -r .ready[]
