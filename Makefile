export FINBOT_EDIT_CMD ?= code --wait
export BLACK_SETTINGS = --exclude 'migrations/|webapp/|venv/' .


alembic-gen:
	tools/check-env.sh message;
	alembic revision --autogenerate -m "${message}"

alembic-upgrade:
	alembic upgrade head

alembic-downgrade:
	alembic downgrade -1

alembic-history:
	alembic history

run-schedsrv-dev:
	tools/autorestart.sh \
		finbot/ \
		python3.9 finbot/apps/schedsrv/schedsrv.py

run-workersrv-dev:
	tools/autorestart.sh \
		finbot/ \
		python3.9 -m celery \
			-A finbot.apps.workersrv.workersrv worker \
			--loglevel INFO

run-histwsrv-dev:
	tools/run-web-service.sh \
		--app histwsrv \
		--timeout 30 \
		--port 5002

run-finbotwsrv-dev:
	tools/run-web-service.sh \
		--app finbotwsrv \
		--workers 4 \
		--timeout 300 \
		--port 5001

run-snapwsrv-dev:
	tools/run-web-service.sh \
		--app snapwsrv \
		--timeout 1200 \
		--port 5000

run-appwsrv-dev:
	tools/run-web-service.sh \
		--app appwsrv \
  		--timeout 600 \
		--port 5003

docker-build-runtime:
	docker build -t finbot/runtime:latest -f runtime.Dockerfile --no-cache .

docker-build-runtime-selenium:
	docker build -t finbot/runtime-selenium:latest -f runtime-selenium.Dockerfile --no-cache .

docker-build: docker-build-runtime docker-build-runtime-selenium

trigger-valuation-docker:
	tools/check-env.sh accounts;
	docker-compose run --rm schedsrv \
		tools/with-env.sh docker \
			make trigger-valuation accounts=${accounts}

trigger-valuation:
	tools/check-env.sh accounts;
	env FINBOT_WAIT_DEPS=db,worker make finbot-wait;
	python3.9 finbot/apps/schedsrv/schedsrv.py \
		--mode one_shot \
		--accounts ${accounts}

test-providers-docker:
	tools/check-env.sh account_id;
	tools/check-env.sh providers;
	docker-compose run --rm operator \
		tools/with-env.sh docker \
			python3.9 tools/providers-tester \
				--dump-balances --dump-assets --dump-liabilities \
				--account-id ${account_id} \
				--providers ${providers}

test-providers-debug:
	tools/check-env.sh account_id;
	tools/check-env.sh providers;
	python3.9 tools/providers-tester \
			--dump-balances --dump-assets --dump-liabilities \
			--show-browser \
			--pause-on-error \
			--no-threadpool \
			--developer-tools \
			--account-id ${account_id} \
			--providers ${providers}

test-providers:
	tools/check-env.sh account_id;
	tools/check-env.sh providers;
	python3.9 tools/providers-tester \
			--dump-balances --dump-assets --dump-liabilities \
			--account-id ${account_id} \
			--providers ${providers}

test-snap:
	tools/check-env.sh account;
	python3.9 tools/snapwsrv-tester \
		--account-id ${account}

test-hist:
	tools/check-env.sh snapshot;
	python3.9 tools/histwsrv-tester \
		--snapshot-id ${snapshot}

run-system-tests-docker:
	env FINBOT_WAIT_DEPS=api,finbot,hist,snap make finbot-wait-docker;
	docker-compose run --rm operator \
		tools/with-env.sh docker \
			python3.9 -m pytest tests/system/

finbotdb-build:
	python3.9 tools/finbotdb build

finbotdb-destroy:
	python3.9 tools/finbotdb destroy

finbotdb-rebuild:
	python3.9 tools/finbotdb destroy && \
	python3.9 tools/finbotdb build

finbotdb-hydrate:
	python3.9 tools/finbotdb hydrate \
		--data-file ./tools/hydrate.json

finbotdb-add-account:
	tools/check-env.sh FINBOT_SECRET_PATH;
	tools/check-env.sh FINBOT_ACCOUNT_PATH;
	python3.9 tools/finbotdb add-account \
		--secret ${FINBOT_SECRET_PATH} \
		--account ${FINBOT_ACCOUNT_PATH}

finbotdb-dump-account:
	tools/check-env.sh FINBOT_SECRET_PATH;
	tools/check-env.sh FINBOT_ACCOUNT_PATH;
	python3.9 tools/finbotdb dump-account \
		--secret ${FINBOT_SECRET_PATH} \
		--account-id ${account_id}

finbotdb-psql:
	tools/check-env.sh FINBOT_DB_PASSWORD;
	tools/check-env.sh FINBOT_DB_HOSTNAME;
	tools/check-env.sh FINBOT_DB_USER;
	tools/check-env.sh FINBOT_DB_DBNAME;
	env PGPASSWORD=${FINBOT_DB_PASSWORD} \
		psql -h ${FINBOT_DB_HOSTNAME} -U ${FINBOT_DB_USER} -d ${FINBOT_DB_DBNAME}

finbot-wait:
	tools/check-env.sh FINBOT_WAIT_DEPS;
	tools/finbot-wait

finbot-wait-docker:
	tools/check-env.sh FINBOT_WAIT_DEPS;
	docker-compose run \
		-e FINBOT_WAIT_DEPS=${FINBOT_WAIT_DEPS} \
		-e FINBOT_WAIT_TIMEOUT=${FINBOT_WAIT_TIMEOUT} \
		--rm operator \
		tools/with-env.sh docker \
			python3.9 tools/finbot-wait

init-dev:
	tools/init-dev.sh

docker-dev:
	docker exec -it operator /bin/bash

py-unit-tests:
	python3.9 -m pytest tests/unit_tests

prettier-ts:
	cd webapp && npm run prettier

tsc-build-check:
	cd webapp && npm run tsc-build-check

prettier-check-ts:
	cd webapp && npm run prettier-check

eslint:
	cd webapp && npm run lint-check:prod

banned-keywords-check-ts:
	tools/banned-keywords.py --source-dirs webapp/src

flake8:
	flake8 --exclude migrations/,venv/ --max-line-length 100

black-check:
	black --check $(BLACK_SETTINGS)

black:
	black $(BLACK_SETTINGS)

mypy:
	mypy -p finbot;
	mypy --strict -p finbot.core;
	mypy --strict -p finbot.clients;
	mypy --strict -p finbot.model;
	mypy --strict -p finbot.providers;

unit-tests-py:
	python3.9 -m pytest -vv tests/unit

unit-tests: unit-tests-py

banned-keywords-check-py:
	tools/banned-keywords.py --source-dirs finbot

lint-sh:
	grep -rl '^#!/.*bash' --exclude-dir=webapp --exclude-dir='./.*' . |\
 		xargs shellcheck -e SC1090 -e SC1091 -S style

lint-py: mypy flake8 black-check banned-keywords-check-py unit-tests-py
lint-ts: eslint tsc-build-check prettier-check-ts banned-keywords-check-ts
lint-all: lint-py lint-ts lint-sh

format-py: black
format-ts: prettier-ts
format-all: format-py format-ts
