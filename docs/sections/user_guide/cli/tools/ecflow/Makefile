.PHONY: all clean

all: help.out realize-help.out realize-stdout.out realize-file.out validate-help.out validate-good.out

clean:
	rm -f *.out
	rm -rf workflow_output

help.out: help.cmd
	bash -c 'cd ../../../../.. && uw ecflow --help' > $@

realize-help.out: realize-help.cmd
	bash -c 'cd ../../../../.. && uw ecflow realize --help' > $@

realize-stdout.out: realize-stdout.cmd ecflow.yaml
	bash -c 'cd ../../../../.. && uw ecflow realize --config-file docs/sections/user_guide/cli/tools/ecflow/ecflow.yaml' > $@

realize-file.out: realize-file.cmd ecflow.yaml
	bash -c 'cd ../../../../.. && rm -rf docs/sections/user_guide/cli/tools/ecflow/workflow_output && uw ecflow realize --config-file docs/sections/user_guide/cli/tools/ecflow/ecflow.yaml --output-dir docs/sections/user_guide/cli/tools/ecflow/workflow_output' > /dev/null 2>&1
	echo "Suite definition and scripts written to workflow_output/" > $@

validate-help.out: validate-help.cmd
	bash -c 'cd ../../../../.. && uw ecflow validate --help' > $@

validate-good.out: validate-good.cmd ecflow.yaml
	bash -c 'cd ../../../../.. && uw ecflow validate --config-file docs/sections/user_guide/cli/tools/ecflow/ecflow.yaml; echo "Exit status: $$?"' > $@
