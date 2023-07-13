#!/bin/bash -eu

# This script is called 1. By conda-build, to test code at package-build time, and 2. By "make test"
# to test code in a live development shell. Its name is dictated by conda-build (see URL below for
# details), but its contents drive from https://github.com/maddenp/condev/tree/main/demo. If run
# with no arguments, it executes all test types: linting, typechecking, unit testing, and basic CLI-
# tool verification. It can also be run with "lint", "typecheck", "unittest", or "cli" arguments to
# run only a single test type. (The "make lint", "make typecheck", and "make unittest" targets in
# the root-directory Makefile run the first test types individually; CLI tools can be hand-tested.)

# https://docs.conda.io/projects/conda-build/en/latest/resources/define-metadata.html#test-section

cli() {
  msg Testing CLI programs
  (
    set -eu
    clis=(
      atparse-to-jinja2
      experiment-manager
      run-forecast
      set-config
      template
      validate-config
    )
    for x in ${clis[*]}; do
      which $x
      $x --help &>/dev/null
    done
  )
  msg OK
}

lint() {
  msg Running linter
  (
    set -eux
    pylint .
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
    coverage run -m pytest -vv .
    coverage report
  )
  msg OK
}

test "${CONDA_BUILD:-}" = 1 && cd ../test_files || cd $(realpath $(dirname $0)/../src)
msg Running in $PWD
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
