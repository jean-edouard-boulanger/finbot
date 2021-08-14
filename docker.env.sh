#!/usr/bin/env bash
SELF_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
source "${SELF_DIR}/secret.env.sh"
source "${SELF_DIR}/tools/bash-utils.sh"

add_to_python_path "${SELF_DIR}"
export FINBOT_DB_HOSTNAME=finbotdb
export FINBOT_DB_USER=finbot
export FINBOT_DB_DBNAME=finbot
export FINBOT_DB_URL="postgresql+psycopg2://${FINBOT_DB_USER}:${FINBOT_DB_PASSWORD}@${FINBOT_DB_HOSTNAME}:5432/${FINBOT_DB_DBNAME}"
export FINBOT_APPWSRV_PORT=5003
export FINBOT_APPWSRV_ENDPOINT=http://appwsrv:${FINBOT_APPWSRV_PORT}/api/v1
export FINBOT_SNAPWSRV_PORT=5000
export FINBOT_SNAPWSRV_ENDPOINT=http://snapwsrv:${FINBOT_SNAPWSRV_PORT}
export FINBOT_FINBOTWSRV_PORT=5001
export FINBOT_FINBOTWSRV_ENDPOINT=http://finbotwsrv:${FINBOT_FINBOTWSRV_PORT}
export FINBOT_HISTWSRV_PORT=5002
export FINBOT_HISTWSRV_ENDPOINT=http://histwsrv:${FINBOT_HISTWSRV_PORT}
export FINBOT_WEBAPP_PORT=5005
export FINBOT_WEBAPP_ENDPOINT=http://webapp:${FINBOT_WEBAPP_PORT}
export FINBOT_SCHEDSRV_PORT=5006
export FINBOT_SCHEDSRV_ENDPOINT="tcp://schedsrv:${FINBOT_SCHEDSRV_PORT}"
