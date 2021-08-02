#!/usr/bin/env bash
OWN_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
source "${OWN_DIR}/bash-utils.sh"


sigint_handler() {
  if [[ -n "${PID}" ]]
  then
    kill -9 "${PID}"
  fi
  exit
}

trap sigint_handler SIGINT

watched="${1}"
shift

log_info "watching directory: ${watched}"
while true
do
  log_info "running: ${*}"
  "$@" &
  app_pid=${!}
  inotifywait -e modify -e move -e create -e delete -e attrib -r "${watched}"
  log_info "changes detected, restarting ..."
  kill -9 "${app_pid}"
done
