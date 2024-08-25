SUBDIRS = $(filter-out ./shared,$(shell find . -maxdepth 1 -mindepth 1 -type d | sort))

.PHONY: all $(SUBDIRS)

all: $(SUBDIRS)

$(SUBDIRS):
	$(MAKE) -C $@ -j
