#!/usr/bin/env bash
SELF_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
source ${SELF_DIR}/secret.env.sh
source ${SELF_DIR}/tools/bash-utils.sh

add_to_python_path ${SELF_DIR}
export FINBOT_VAULT_PATH=${SELF_DIR}/.secure
export FINBOT_SECRET_PATH=${FINBOT_VAULT_PATH}/secret.txt
export FINBOT_ACCOUNT_PATH=${FINBOT_VAULT_PATH}/accounts
export FINBOT_DB_HOSTNAME=finbotdb
export FINBOT_DB_USER=finbot
export FINBOT_DB_DBNAME=finbot
export FINBOT_DB_URL=postgresql+psycopg2://${FINBOT_DB_USER}:${FINBOT_DB_PASSWORD}@${FINBOT_DB_HOSTNAME}:5432/${FINBOT_DB_DBNAME}
export FINBOT_SNAPWSRV_ENDPOINT=http://snapwsrv:5000
export FINBOT_FINBOTWSRV_ENDPOINT=http://finbotwsrv:5001
export FINBOT_HISTWSRV_ENDPOINT=http://histwsrv:5002
export FINBOT_APPWSRV_ENDPOINT=http://appwsrv:5003
export FINBOT_WEBAPP_ENDPOINT=
export FINBOT_SCHEDSRV_PORT=5006
export FINBOT_SCHEDSRV_ENDPOINT=tcp://schedsrv:${FINBOT_SCHEDSRV_PORT}