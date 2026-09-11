abort() {
  trap EXIT # unset previous trap
  ecflow_client --abort=$ECF_RID
  exit 1
}

trap abort ERR SIGTERM

complete() {
  ecflow_client --complete
}

trap complete EXIT

init() {
  export ECF_RID=$1
  ecflow_client --init=$ECF_RID
}

set -euxo pipefail
