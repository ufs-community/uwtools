rm -f suite.def
uw ecflow realize --config-file ecflow.yaml --output-dir .
echo
cat suite.def
