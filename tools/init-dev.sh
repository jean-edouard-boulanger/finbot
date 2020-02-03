#!/usr/bin/env bash
OWN_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
yes_no=${OWN_DIR}/yes_no

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

log_info checking docker availability
which docker >/dev/null 2>&1 || die "'docker' is not available in this machine, install and try again"

log_info checking docker-compose availability
which docker-compose  >/dev/null 2>&1 || die "'docker-compose' is not available on this machine, install and try again"

if [[ "${rebuild_images}" == "1" ]]
then
    log_info "Will re-build all finbot containers from scratch"
    docker-compose build --no-cache
fi

log_info "Starting development container"
docker-compose up -d dev

[[ -n "${FINBOT_VAULT_PATH}" ]] || die "FINBOT_VAULT_PATH is not set"
if [[ ! -d ${FINBOT_VAULT_PATH} ]]
then
    log_info "Vault does not exist, will initialize"
    docker exec dev make init-vault
fi

[[ -n "${FINBOT_ACCOUNT_PATH}" ]] || die "FINBOT_ACCOUNT_PATH is not set"
if [[ ! -f ${FINBOT_ACCOUNT_PATH} ]]
then
    log_info "Development account does not exist, will create"
    docker exec dev make init-account
fi

log_info "Waiting for finbotdb to be reachable"
docker exec dev make finbotdb-wait

log_info "Will rebuild finbotdb schema from model"
docker exec dev make finbotdb-rebuild

log_info "Hydrating finbotdb with default data"
docker exec dev make finbotdb-hydrate

log_info "Adding development account to finbotdb"
docker exec dev make finbotdb-add-account

log_info "The development environment is ready"

echo
echo "> You can start all containers with 'docker-compose up'"
echo "> You can stop all containers with 'docker-compose down'"
echo "> After starting the containers, the finbot web application will shortly be accessible from http://127.0.0.1:5005"
echo "> All applications will be restarted automatically on code change in webapp/ and finbot/"
