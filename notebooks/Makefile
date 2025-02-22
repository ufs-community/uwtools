TARGETS = format lint test-nb unittest

.PHONY: $(TARGETS)

all:
	$(error Valid targets are: $(TARGETS))

format:
	black tests
	isort tests

lint:
	pylint tests

test: test-nb

test-nb: lint unittest

unittest:
	pytest tests
