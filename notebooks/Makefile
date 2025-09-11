TARGETS = format lint notebook test-nb unittest

.PHONY: $(TARGETS)

all:
	$(error Valid targets are: $(TARGETS))

format:
	ruff format tests
	ruff check --select I --fix tests

lint:
	ruff check tests

notebook:
	TZ=UTC FAKE_NOW=True jupyter nbconvert --to notebook --inplace --execute *.ipynb
	jupyter nbconvert --to notebook --coalesce-streams --inplace --ClearMetadataPreprocessor.enabled=True --ClearNotebookMetadataPreprocessor.enabled=True *.ipynb

test: test-nb

test-nb: lint unittest

unittest:
	pytest -vv tests
