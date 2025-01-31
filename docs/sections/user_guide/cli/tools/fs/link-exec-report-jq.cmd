rm -rf link-dst-report-jq
uw fs link --report --target-dir link-dst-report-jq --config-file link-config-report.yaml 2>/dev/null | jq -r .ready[]
