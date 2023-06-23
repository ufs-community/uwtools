#!/bin/bash -eu

cli() {
  echo Testing CLI programs:
  (
    set -eu
    clis=(
      heythere
    )
    for x in ${clis[*]}; do
      which $x
    done
  )
  echo OK
}

lint() {
  echo Running linter:
  (
    set -eux
    pylint ${pyfiles[*]}
  )
  echo OK
}

typecheck() {
  echo Running typechecker:
  (
    set -eux
    mypy --install-types --non-interactive ${pyfiles[*]}
  )
  echo OK
}

unittest() {
  echo Running unit tests:
  (
    set -eux
    coverage run -m pytest -v $srcdir/test
    coverage report
  )
  echo OK
}

test "${CONDA_BUILD:-}" = 1 && srcdir=$PWD || srcdir=$(realpath $(dirname $0)/../src)
pyfiles=( $(find $srcdir -type f -name "*.py") )
if [[ -n "${1:-}" ]]; then
  $1 # run single specified code-quality tool
else
  lint
  typecheck
  unittest
  cli
fi
