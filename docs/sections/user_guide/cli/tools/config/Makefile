COMMANDS = $(wildcard *.cmd)
OUTPUTS  = $(COMMANDS:cmd=out)

.PHONY: all $(OUTPUTS)

all: $(OUTPUTS)

$(OUTPUTS):
	$$(cat $(basename $@).cmd) >$@ 2>&1 | true
