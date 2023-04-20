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
if [ $status -ne 0 ] ; then
  echo "pytest failed"
  exit 1
fi

# Lint
pylint --ignore-imports=y tests scripts
status=$?
if [ $status -ne 0 ] ; then
  echo "linting tests and scripts failed"
  exit 1
fi

cd ${WORKSPACE}/src
pylint uwtools
status=$?
if [ $status -ne 0 ] ; then
  echo "linting uwtools failed"
  exit 1
fi
