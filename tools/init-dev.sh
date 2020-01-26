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

[[ -n "${FINBOT_VAULT_PATH}" ]] || die "FINBOT_VAULT_PATH is not set"
if [[ ! -d ${FINBOT_VAULT_PATH} ]]
then
    log_info "Vault does not exist, will initialize"
    make init-vault
fi

[[ -n "${FINBOT_ACCOUNT_PATH}" ]] || die "FINBOT_ACCOUNT_PATH is not set"
if [[ ! -f ${FINBOT_ACCOUNT_PATH} ]]
then
    log_info "Development account does not exist, will create"
    make init-account
fi

log_info "Will build finbot containers"
#docker-compose build

log_info "Starting database and development container"
docker-compose up -d finbotdb dev

log_info "Waiting for finbotdb to be reachable"
docker exec -it dev make finbotdb-wait

log_info "Will rebuild finbotdb schema from model"
docker exec -it dev make finbotdb-rebuild

log_info "Hydrating finbotdb with default data"
docker exec -it dev make finbotdb-hydrate

log_info "Adding development account to finbotdb"
docker exec -it dev make finbotdb-add-account

log_info "Starting all finbot services in docker"
docker-compose up -d

log_info "Finbot web application will soon be accessible from http://127.0.0.1:5005"
log_info "You can stop all containers with 'docker-compose down'"
log_info "You can start all containers with 'docker-compose up'"
log_info "All applications will be restarted automatically on code change in webapp/ and finbot/"
log_info "All done"

if ${yes_no} "monitor finbot services?"
then
    log_info "^C (CTRL+C) to leave"
    docker-compose logs -f
else
    log_info "you can monitor finbot services later by running 'docker-compose logs -f'"
fi
