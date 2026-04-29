rm -f suite.def
uw ecflow realize --config-file ecflow.yaml --output-path .
echo
cat suite.def
