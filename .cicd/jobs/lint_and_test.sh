#!/bin/bash -ux

# Setup PYTHONPATH for uwtools
export PYTHONPATH=${PWD}:${PWD}/src

# Check for pytest and pylint
for pkg in pytest pylint ; do
  if hash $pkg  2>/dev/null; then
    echo "$pkg installed, moving on!".
  else
    echo "$pkg is not installed"
    exit 1
  fi
done

# Run tests
pytest -k "not test_validate_yaml_salad" | tee -a ${WORKSPACE}/results.txt
status=${PIPESTATUS[0]}
test $status == 0 || ( echo "pytest failed" && exit $status )

# Lint
pylint --ignore-imports=y tests scripts src/uwtools
status=$?
test $status == 0 || ( echo "linting failed" && exit $status )

