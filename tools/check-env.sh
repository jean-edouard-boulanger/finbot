#!/usr/bin/env bash
env_var=${1}
if [[ "${!env_var}" == "" ]]
then
  echo "!! required environment variable '${env_var}' is not set"
  exit 1
fi
exit 0
