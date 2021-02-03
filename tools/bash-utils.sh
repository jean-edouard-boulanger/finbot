#!/usr/bin/env bash


log () {
  log_level=$1
  shift
  >&2 echo "$(date) [ ${log_level} ] ${@}"
}
log_info () { log INFO $@; }
log_warn () { log WARN $@; }
log_error () { log ERROR $@; }
die () {
  log_error ${@}
  exit 1
}
docker_image_exists () {
  if [[ "$(docker images -q $1 2> /dev/null)" == "" ]]
  then
    return 1
  fi
  return 0
}
