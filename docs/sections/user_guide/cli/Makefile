SUBDIRS = $(shell find . -maxdepth 1 -mindepth 1 -type d)

.PHONY: all $(SUBDIRS)

all: $(SUBDIRS)

$(SUBDIRS):
	$(MAKE) -C $@ -j
