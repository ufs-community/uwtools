#!/bin/bash -eu

cli() {
  echo Testing CLI programs:
  (
    set -eu
    clis=(
      atparse-to-jinja2
      run-forecast
      set-config
      template
    )
    for x in ${clis[*]}; do
      which $x
      $x --help &>/dev/null
    done
  )
  echo OK
}

lint() {
  echo Running linter...
  (
    set -eu
    pylint ${pyfiles[*]}
  )
  echo OK
}

typecheck() {
  echo Running typechecker...
  (
    set -eu
    mypy --install-types --non-interactive ${pyfiles[*]}
  )
  echo OK
}

unittest() {
  echo Running unit tests...
  (
    set -eux
    coverage run -m pytest -vv $srcdir
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
