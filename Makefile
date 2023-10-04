CHANNELS    = $(addprefix -c ,$(shell tr '\n' ' ' <$(RECIPE_DIR)/channels)) -c local
METAJSON    = $(RECIPE_DIR)/meta.json
RECIPEFILES = $(addprefix $(RECIPE_DIR)/,conda_build_config.yaml meta.yaml)
TARGETS     = devshell env format lint meta package test typecheck unittest

export RECIPE_DIR := $(shell cd ./recipe && pwd)

spec = $(call val,name)$(2)$(call val,version)$(2)$(call val,$(1))
val  = $(shell jq -r .$(1) $(METAJSON))

.PHONY: $(TARGETS)

all:
	$(error Valid targets are: $(TARGETS))

devshell:
	condev-shell || true

env: package
	conda create -y -n $(call spec,buildnum,-) $(CHANNELS) $(call spec,build,=)

format:
	@echo "=> Running formatters"
	black src
	isort src
	cd src && docformatter . || test $$? -eq 3
	for x in $$(find src -type f -name "*.jsonschema"); do jq -S . $$x >$$x.tmp && mv $$x.tmp $$x || rm $$x.tmp; done

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
