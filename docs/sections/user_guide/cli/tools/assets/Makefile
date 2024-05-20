COMMANDS = $(wildcard *.cmd)
OUTPUTS  = $(COMMANDS:cmd=out)

.PHONY: all

all: $(OUTPUTS)

%.out: %.cmd
	$$(cat $<) >$@
