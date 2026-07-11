ROOT = $(shell git rev-parse --show-toplevel)

.PHONY: all

all: ecflow.html

ecflow.html: $(ROOT)/notebooks/ecflow/ecflow.ipynb
	jupyter nbconvert --output-dir=. --to html $<
