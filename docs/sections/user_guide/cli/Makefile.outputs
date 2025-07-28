export UWTOOLS_TIMESTAMP = 2025-01-02T03:04:05

COMMANDS = $(wildcard *.cmd)
OUTPUTS  = $(COMMANDS:cmd=out)

.PHONY: all $(OUTPUTS)

all: $(OUTPUTS)

$(OUTPUTS):
	@bash $(basename $@).cmd >$@ 2>&1 | true

# The following targets support semi-automated output generation: They will not run automatically,
# but can be manually invoked (e.g. "make foo.out" given a "foo.txt" command file) to update .out
# files. They must be invoked in a context where all commands in the .txt file are available, e.g.
# on an HPC where the "hsi" or "rocotorun" commands are on PATH, if those are ultimately called by
# the recipe.

%.out: %.txt %.yaml
	@bash $< >$@ 2>&1 | true

%.out: %.txt
	@bash $< >$@ 2>&1 | true
