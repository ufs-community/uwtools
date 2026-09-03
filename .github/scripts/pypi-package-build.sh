#!/bin/bash -eux

. $(dirname ${BASH_SOURCE[0]})/common.sh
ci_conda_activate
unset CONDEV_SHELL
set -ux
python -m build --no-isolation --wheel src
