#!/usr/bin/env bash
SELF_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
source "${SELF_DIR}/bash-utils.sh"

git config --global --add safe.directory "*"
top_level=$(git rev-parse --show-toplevel)
webapp_dir="${top_level}/webapp"
log_info "finbot web application is located in ${webapp_dir}"
cd "${webapp_dir}" || die "could not cd"

log_info "running 'npm install' to update packages"
npm install
npm run start
