#!/usr/bin/env bash
SELF_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
source "${SELF_DIR}/bash-utils.sh"

finbot_env=${FINBOT_ENV:-production}
workers=1

while [[ $# -gt 0 ]]
do
  key="$1"
  case $key in
    --env)
      finbot_env="$2"
      shift 2
    ;;
    --app)
      app_name="$2"
      shift 2
    ;;
    --port)
      port="$2"
      shift 2
    ;;
    --workers)
      workers="$2"
      shift 2
    ;;
    *)
      echo "unknown argument: ${key}"
      exit 1
    ;;
  esac
done

[[ -n "${finbot_env}" ]] || die "--env (environment) must be specified"
[[ -n "${app_name}" ]] || die "--app (application name) must be specified"
[[ -n "${port}" ]] || die "--port must be specified"

uvicorn_log_config_path="/tmp/uvicorn_log_config.json"
echo '{"version": 1, "disable_existing_loggers": false}' > "${uvicorn_log_config_path}"

if [[ "${finbot_env}" == "development" ]]
then
  echo "running ${app_name} with dev uvicorn (environment: ${finbot_env})"
  run_and_trace \
    watchmedo auto-restart \
      --directory finbot/ \
      --pattern '*.py' \
      --recursive \
      --signal SIGKILL \
        -- uvicorn "finbot.apps.${app_name}.${app_name}:app" \
          --port "${port}" \
          --host 0.0.0.0 \
          --workers "${workers}" \
          --log-config "${uvicorn_log_config_path}"
else
  echo "running ${app_name} with uvicorn (environment: ${finbot_env})"
  run_and_trace uvicorn "finbot.apps.${app_name}.${app_name}:app" \
    --port "${port}" \
    --host 0.0.0.0 \
    --workers "${workers}" \
    --log-config "${uvicorn_log_config_path}"
fi
