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
pytest | tee -a ${WORKSPACE}/results.txt
status=${PIPESTATUS[0]}
test $status -ne 0 && echo "pytest failed" && exit 1

# Lint
pylint --ignore-imports=y tests scripts
status=$?
test $status -ne 0 && echo "linting tests failed" && exit 1

cd ${WORKSPACE}/src
pylint uwtools
status=$?
test $status -ne 0 && echo "linting tools failed" && exit 1
