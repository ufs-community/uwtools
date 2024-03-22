CHANNELS    = $(addprefix -c ,$(shell tr '\n' ' ' <$(RECIPE_DIR)/channels)) -c local
METAJSON    = $(RECIPE_DIR)/meta.json
RECIPEFILES = $(addprefix $(RECIPE_DIR)/,meta.yaml)
TARGETS     = clean-devenv devshell docs env format lint meta package test typecheck unittest


export RECIPE_DIR := $(shell cd ./recipe && pwd)

clean = $(info $(shell $(CONDA_EXE) env remove -y -n DEV-$(call val,name)))
spec  = $(call val,name)$(2)$(call val,version)$(2)$(call val,$(1))
val   = $(shell jq -r .$(1) $(METAJSON))

.PHONY: $(TARGETS)

all:
	$(error Valid targets are: $(TARGETS))

clean-devenv:
	$(if $(filter DEV-$(call val,name),$(CONDA_DEFAULT_ENV)),$(error EXIT DEVSHELL FIRST),$(call clean))

devshell:
	condev-shell || true

docs:
	$(MAKE) -C docs docs

env: package
	conda create -y -n $(call spec,buildnum,-) $(CHANNELS) $(call spec,build,=)

format:
	@./format

lint:
	recipe/run_test.sh lint

meta: $(METAJSON)

package: meta
	conda build $(CHANNELS) --error-overlinking --override-channels $(RECIPE_DIR)

test:
	recipe/run_test.sh

typecheck:
	recipe/run_test.sh typecheck

unittest:
	recipe/run_test.sh unittest

$(METAJSON): $(RECIPEFILES)
	condev-meta
