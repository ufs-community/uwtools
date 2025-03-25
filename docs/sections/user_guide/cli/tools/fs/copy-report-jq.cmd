rm -rf dst/copy-report-jq
uw fs copy --report --target-dir dst/copy-report-jq --config-file copy-report.yaml 2>/dev/null | jq -r .ready[]
