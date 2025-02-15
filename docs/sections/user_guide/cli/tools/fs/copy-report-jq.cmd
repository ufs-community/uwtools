rm -rf dst/copy
uw fs copy --report --target-dir dst/copy --config-file copy-report.yaml 2>/dev/null | jq -r .ready[]
