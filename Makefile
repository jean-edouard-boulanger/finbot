export FINBOT_EDIT_CMD ?= code --wait


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
	env FLASK_APP=finbot/apps/histwsrv/histwsrv.py \
		FLASK_ENV=development \
		flask run \
			--port 5002 \
			--without-threads \
			--extra-files 'finbot/**/*.py' \
			-h 0.0.0.0

run-finbotwsrv-dev:
	env FLASK_APP=finbot/apps/finbotwsrv/finbotwsrv.py \
		FLASK_ENV=development \
		flask run \
			--port 5001 \
			--with-threads \
			--extra-files 'finfinbot/**/*.py' \
			-h 0.0.0.0

run-snapwsrv-dev:
	env FLASK_APP=finbot/apps/snapwsrv/snapwsrv.py \
		FLASK_ENV=development \
		flask run \
			--port 5000 \
			--without-threads \
			--extra-files 'finbot/**/*.py' \
			-h 0.0.0.0

run-appwsrv-dev:
	env FLASK_APP=finbot/apps/appwsrv/appwsrv.py \
		FLASK_ENV=development \
		flask run \
			--port 5003 \
			--without-threads \
			--extra-files 'finbot/**/*.py' \
			-h 0.0.0.0

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
	python3.9 finbot/apps/schedsrv/schedsrv.py \
		--mode one_shot \
		--accounts ${accounts}

test-providers-docker:
	tools/check-env.sh providers;
	docker-compose run --rm operator \
		tools/with-env.sh docker \
			python3.9 tools/providers-tester \
				--dump-balances --dump-assets --dump-liabilities \
				--providers ${providers}

test-providers-debug:
	tools/check-env.sh providers;
	python3.9 tools/providers-tester \
			--dump-balances --dump-assets --dump-liabilities \
			--show-browser \
			--pause-on-error \
			--no-threadpool \
			--developer-tools \
			--providers ${providers}

test-providers:
	tools/check-env.sh providers;
	python3.9 tools/providers-tester \
			--dump-balances --dump-assets --dump-liabilities \
			--providers ${providers}

test-snap:
	tools/check-env.sh account;
	python3.9 tools/snapwsrv-tester \
		--account-id ${account}

test-hist:
	tools/check-env.sh snapshot;
	python3.9 tools/histwsrv-tester \
		--snapshot-id ${snapshot}

init-vault:
	tools/init-vault.sh

init-account:
	tools/check-env.sh FINBOT_SECRET_PATH;
	tools/check-env.sh FINBOT_ACCOUNT_PATH;
	python3.9 tools/crypt fernet-encrypt \
		-k ${FINBOT_SECRET_PATH} \
		-i tools/accounts.tpl.json > ${FINBOT_ACCOUNT_PATH} && \
	echo "created default account, run 'make edit-account' to configure"

show-account:
	tools/check-env.sh FINBOT_SECRET_PATH;
	tools/check-env.sh FINBOT_ACCOUNT_PATH;
	python3.9 tools/crypt fernet-decrypt \
		-k ${FINBOT_SECRET_PATH} \
		-i ${FINBOT_ACCOUNT_PATH} | less

edit-account:
	tools/check-env.sh FINBOT_SECRET_PATH;
	tools/check-env.sh FINBOT_ACCOUNT_PATH;
	python3.9 tools/crypt fernet-decrypt \
		-k ${FINBOT_SECRET_PATH} \
		-i ${FINBOT_ACCOUNT_PATH} > .accounts.tmp.json && \
	chmod 600 .accounts.tmp.json && \
	${FINBOT_EDIT_CMD} .accounts.tmp.json && \
	python3.9 tools/crypt fernet-encrypt \
		-k ${FINBOT_SECRET_PATH} \
		-i .accounts.tmp.json > ${FINBOT_ACCOUNT_PATH} && \
	rm .accounts.tmp.json

finbotdb-build:
	python3.9 tools/finbotdb build

finbotdb-destroy:
	python3.9 tools/finbotdb destroy

finbotdb-rebuild:
	python3.9 tools/finbotdb destroy && \
	python3.9 tools/finbotdb build

finbotdb-hydrate:
	python3.9 tools/finbotdb --database hydrate \
		--data-file ./tools/hydrate.json

finbotdb-add-account:
	tools/check-env.sh FINBOT_SECRET_PATH;
	tools/check-env.sh FINBOT_ACCOUNT_PATH;
	python3.9 tools/finbotdb --database add-account \
		--secret ${FINBOT_SECRET_PATH} \
		--account ${FINBOT_ACCOUNT_PATH}

finbotdb-dump-account:
	tools/check-env.sh FINBOT_SECRET_PATH;
	tools/check-env.sh FINBOT_ACCOUNT_PATH;
	python3.9 tools/finbotdb --database dump-account \
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
	tools/finbot-wait

init-dev:
	tools/init-dev.sh

docker-dev:
	docker exec -it operator /bin/bash

unit-tests:
	python3.9 -m pytest tests/unit_tests
