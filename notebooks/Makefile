TARGETS = format lint test-nb unittest

.PHONY: $(TARGETS)

all:
	$(error Valid targets are: $(TARGETS))

format:
	ruff format tests
	ruff check --select I --fix tests

lint:
	ruff check tests

test: test-nb

test-nb: lint unittest

unittest:
	pytest -vv tests
