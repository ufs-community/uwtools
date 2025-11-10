set -ae
. $(dirname ${BASH_SOURCE[0]})/common.sh
ci_conda_activate

validate_driver_configs() {
  for config in docs/shared/drivers/*.yaml; do
    driver=$(basename ${config%.yaml})
    basecmd="uw $driver validate"
    args=( --config $config )
    $basecmd --help | grep -q -- "--cycle" && args+=( --cycle 1970-01-01T00:00:00 )
    $basecmd --help | grep -q -- "--leadtime" && args+=( --leadtime 6 )
    ( set -x && $basecmd ${args[*]} )
  done
}

CONDEV_SHELL_CMD=validate_driver_configs condev-shell
