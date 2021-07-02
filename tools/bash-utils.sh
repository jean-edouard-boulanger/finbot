#!/usr/bin/env bash

log() {
  log_level=$1
  shift
  echo >&2 "$(date) [ ${log_level} ] ${@}"
}
log_info() { log INFO $@; }
log_warn() { log WARN $@; }
log_error() { log ERROR $@; }
die() {
  log_error ${@}
  exit 1
}
docker_image_exists() {
  if [[ "$(docker images -q $1 2>/dev/null)" == "" ]]; then
    return 1
  fi
  return 0
}
docker_run_operator() {
  echo $@
  docker-compose run --rm operator \
    tools/with-env.sh docker $@
}
add_to_python_path() {
  value=$1
  if [ -d "${value}" ] && [[ ":${PATH}:" != *":${value}:"* ]]; then
    export PYTHONPATH="${PYTHONPATH:+"$PATH:"}$1"
  fi
}
run() {
  echo "running: $@"
  exec $@
}
