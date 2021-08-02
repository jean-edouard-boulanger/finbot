export FINBOT_EDIT_CMD ?= code --wait
export BLACK_SETTINGS = --exclude migrations/ webapp/ .


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
		finbot/apps/schedsrv \
		python3.9 finbot/apps/schedsrv/schedsrv.py

run-histwsrv-dev:
	tools/run-web-app.sh \
		--app histwsrv \
		--timeout 30 \
		--port 5002

run-finbotwsrv-dev:
	tools/run-web-app.sh \
		--app finbotwsrv \
		--workers 4 \
		--timeout 300 \
		--port 5001

run-snapwsrv-dev:
	tools/run-web-app.sh \
		--app snapwsrv \
		--timeout 1200 \
		--port 5000

run-appwsrv-dev:
	tools/run-web-app.sh \
		--app appwsrv \
  		--timeout 5 \
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
	env FINBOT_WAIT_DEPS=db,snap,hist make finbot-wait;
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

js-prettier:
	cd webapp && npm run prettier

js-prettier-check:
	cd webapp && npm run prettier-check

js-eslint:
	cd webapp && npm run lint-check:prod

js-banned-keywords-check:
	tools/banned-keywords.py --source-dirs webapp/src

py-flake8:
	flake8 --exclude migrations/ --max-line-length 100

py-black-check:
	black --check $(BLACK_SETTINGS)

py-black:
	black $(BLACK_SETTINGS)

py-mypy:
	mypy -p finbot;
	mypy --strict -p finbot.core;
	mypy --strict -p finbot.model;
	mypy --strict -p finbot.apps.support;

py-banned-keywords-check:
	tools/banned-keywords.py --source-dirs finbot

py-lint: py-mypy py-flake8 py-black-check py-banned-keywords-check
js-lint: js-eslint js-prettier-check js-banned-keywords-check
lint: py-lint js-lint

py-format: py-black
js-format: js-prettier
format: py-format js-format
