rm -f suite.def
uw ecflow realize --config-file workflow.yaml --output-dir .
cat suite.def
