#!/usr/bin/env bash
SELF_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
source "${SELF_DIR}/bash-utils.sh"

finbot_env=${FINBOT_ENV:-production}
workers=1
timeout=30

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
    --timeout)
      timeout="$2"
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

if [[ "${finbot_env}" == "development" ]]
then
  echo "running ${app_name} with flask (environment: ${finbot_env})"
  export FLASK_APP=finbot/apps/${app_name}/${app_name}.py
  export FLASK_ENV=development
  threads_args="--without-threads"
  if [[ "${workers}" -gt 1 ]]
  then
    threads_args="--with-threads"
  fi
  run_and_trace flask run \
			--port "${port}" \
			"${threads_args}" \
			-h 0.0.0.0 \
			--extra-files 'finbot/\*\*/\*.py'
else
  echo "running ${app_name} with gunicorn (environment: ${finbot_env})"
  run_and_trace gunicorn \
    "finbot.apps.${app_name}.${app_name}:app" \
      --workers "${workers}" \
      --timeout "${timeout}" \
      --bind "0.0.0.0:${port}"
fi
