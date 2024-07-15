#!/bin/bash -eu

# This script is called 1. By conda-build, to test code at package-build time, and 2. By "make test"
# to test code in a live development shell. Its name is dictated by conda-build (see URL below for
# details), but its contents derive from https://github.com/maddenp/condev/tree/main/demo. If run
# with no arguments, it executes all test types: linting, typechecking, unit testing, and basic CLI-
# tool verification. It can also be run with "lint", "typecheck", "unittest", or "cli" arguments to
# run only a single test type. (The "make lint", "make typecheck", and "make unittest" targets in
# the root-directory Makefile run the first test types individually; CLI tools can be hand-tested.)

# https://docs.conda.io/projects/conda-build/en/latest/resources/define-metadata.html#test-section

cli() {
  msg Testing CLI
  (
    set -eux
    uw --version
  )
  msg OK
}

lint() {
  msg Running linter
  (
    set -eux
    pylint -j 4 .
  )
  msg OK
}

msg() {
  echo "=> $@"
}

typecheck() {
  msg Running typechecker
  (
    set -eux
    mypy --install-types --non-interactive .
  )
  msg OK
}

unittest() {
  msg Running unit tests
  (
    set -eux
    pytest --cov=uwtools -n 4 .
  )
  msg OK
}

test "${CONDA_BUILD:-}" = 1 && cd ../test_files || cd $(dirname $0)/../src
if [[ -n "${1:-}" ]]; then
  # Run single specified code-quality tool.
  $1
else
  # Run all code-quality tools.
  lint
  typecheck
  unittest
  cli
fi
