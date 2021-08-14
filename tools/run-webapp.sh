#!/usr/bin/env bash
SELF_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
source "${SELF_DIR}/bash-utils.sh"

finbot_env=${FINBOT_ENV:-production}

webapp_dir="${FINBOT_TOPLEVEL_DIR}/webapp"
log_info "finbot web application is located in ${webapp_dir}"
cd "${webapp_dir}"

log_info "running 'npm install' to update packages"
npm install

if [[ "${finbot_env}" == "development" ]]
then
  log_info "running webapp with a development build"
  npm run start
else
  log_info "running webapp with an optimized production build"
  npm run build
  npm run serve -- -l tcp://0.0.0.0:${FINBOT_WEBAPP_PORT}
fi
