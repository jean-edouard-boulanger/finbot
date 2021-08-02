#!/usr/bin/env bash
OWN_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
source "${OWN_DIR}/bash-utils.sh"

[[ -n "${FINBOT_VAULT_PATH}" ]] || die "FINBOT_VAULT_PATH is not set"
[[ -n "${FINBOT_SECRET_PATH}" ]] || die "FINBOT_SECRET_PATH is not set"

if [[ ! -d "${FINBOT_VAULT_PATH}" ]]
then
  log_info "creating ${FINBOT_VAULT_PATH}"
	mkdir -p "${FINBOT_VAULT_PATH}"
  log_info "generating secret key in ${FINBOT_SECRET_PATH}"
	python3.9 tools/crypt fernet-key > "${FINBOT_SECRET_PATH}"
	chmod 600 "${FINBOT_SECRET_PATH}"
else
  log_info "${FINBOT_VAULT_PATH} already exists, not overriding"
fi
