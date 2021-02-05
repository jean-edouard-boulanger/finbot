export PYTHONPATH := $(PYTHONPATH):$(shell pwd)
export FINBOT_VAULT_PATH ?= .secure
export FINBOT_SECRET_PATH ?= $(FINBOT_VAULT_PATH)/secret.txt
export FINBOT_ACCOUNT_PATH ?= $(FINBOT_VAULT_PATH)/accounts
export FINBOT_DB_PORT ?= 5432
export FINBOT_DB_HOSTNAME ?= 127.0.0.1
export FINBOT_DB_USER ?= finbot
export FINBOT_DB_PASSWORD ?= finbot
export FINBOT_DB_DBNAME ?= finbot
export FINBOT_DB_URL := postgresql+psycopg2://${FINBOT_DB_USER}:${FINBOT_DB_PASSWORD}@${FINBOT_DB_HOSTNAME}:${FINBOT_DB_PORT}/${FINBOT_DB_DBNAME}
export FINBOT_SNAPWSRV_ENDPOINT ?= http://127.0.0.1:5000
export FINBOT_FINBOTWSRV_ENDPOINT ?= http://127.0.0.1:5001
export FINBOT_HISTWSRV_ENDPOINT ?= http://127.0.0.1:5002
export FINBOT_APPWSRV_ENDPOINT ?= http://127.0.0.1:5003
export FINBOT_WEBAPP_ENDPOINT ?= http://127.0.0.1:5005
export FINBOT_SCHEDSRV_PORT ?= 5006
export FINBOT_SCHEDSRV_ENDPOINT ?= tcp://127.0.0.1:${FINBOT_SCHEDSRV_PORT}
export FINBOT_EDIT_CMD ?= code --wait

info:
	$(info PYTHONPATH=${PYTHONPATH})
	$(info FINBOT_SECRET_PATH=${FINBOT_SECRET_PATH})
	$(info FINBOT_ACCOUNT_PATH=${FINBOT_ACCOUNT_PATH})
	$(info FINBOT_DB_PORT=${FINBOT_DB_PORT})
	$(info FINBOT_DB_HOSTNAME=${FINBOT_DB_HOSTNAME})
	$(info FINBOT_DB_USER=${FINBOT_DB_USER})
	$(info FINBOT_DB_PASSWORD=${FINBOT_DB_PASSWORD})
	$(info FINBOT_DB_DBNAME=${FINBOT_DB_DBNAME})
	$(info FINBOT_DB_URL=${FINBOT_DB_URL})
	$(info FINBOT_FINBOTWSRV_ENDPOINT=${FINBOT_FINBOTWSRV_ENDPOINT})
	$(info FINBOT_SNAPWSRV_ENDPOINT=${FINBOT_SNAPWSRV_ENDPOINT})
	$(info FINBOT_HISTWSRV_ENDPOINT=${FINBOT_HISTWSRV_ENDPOINT})
	$(info FINBOT_SCHEDSRV_PORT=${FINBOT_SCHEDSRV_PORT})
	$(info FINBOT_SCHEDSRV_ENDPOINT=${FINBOT_SCHEDSRV_ENDPOINT})

alembic-gen:
	alembic revision --autogenerate -m "${message}"

alembic-upgrade:
	alembic upgrade head

alembic-downgrade:
	alembic downgrade -1

alembic-history:
	alembic history

run-schedsrv-dev:
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
	docker-compose run schedsrv \
		make trigger-valuation accounts=${accounts}

trigger-valuation:
	python3.9 finbot/apps/schedsrv/schedsrv.py \
		--mode one_shot \
		--accounts ${accounts}

test-providers-docker:
	docker run \
		-v $(shell pwd):/finbot \
		--workdir /finbot \
		--env PYTHONPATH='${PYTONPATH}:/finbot' \
		--rm -it \
		finbot/runtime-selenium:latest \
		python3.9 tools/providers-tester \
			--dump-balances --dump-assets --dump-liabilities --dump-transactions \
			--secret-file ${FINBOT_SECRET_PATH} \
			--accounts-file ${FINBOT_ACCOUNT_PATH} \
			--providers ${providers}

test-providers-debug:
	python3.9 tools/providers-tester \
			--dump-balances --dump-assets --dump-liabilities --dump-transactions \
			--secret-file ${FINBOT_SECRET_PATH} \
			--accounts-file ${FINBOT_ACCOUNT_PATH} \
			--show-browser \
			--pause-on-error \
			--no-threadpool \
			--developer-tools \
			--providers ${providers}

test-providers:
	python3.9 tools/providers-tester \
			--dump-balances --dump-assets --dump-liabilities --dump-transactions \
			--secret-file ${FINBOT_SECRET_PATH} \
			--accounts-file ${FINBOT_ACCOUNT_PATH} \
			--providers ${providers}

test-snapwsrv:
	python3.9 tools/snapwsrv-tester \
		--endpoint ${FINBOT_SNAPWSRV_ENDPOINT} \
		--account-id ${ACCOUNT_ID}

test-histwsrv:
	python3.9 tools/histwsrv-tester \
		--endpoint ${FINBOT_HISTWSRV_ENDPOINT} \
		--snapshot-id ${SNAPSHOT_ID}

init-vault:
	tools/init-vault.sh

init-account:
	python3.9 tools/crypt fernet-encrypt \
		-k ${FINBOT_SECRET_PATH} \
		-i tools/accounts.tpl.json > ${FINBOT_ACCOUNT_PATH} && \
	echo "created default account, run 'make edit-account' to configure"

show-account:
	python3.9 tools/crypt fernet-decrypt \
		-k ${FINBOT_SECRET_PATH} \
		-i ${FINBOT_ACCOUNT_PATH} | less

edit-account:
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
	python3.9 tools/finbotdb --database ${FINBOT_DB_URL} build

finbotdb-destroy:
	python3.9 tools/finbotdb --database ${FINBOT_DB_URL} destroy

finbotdb-rebuild:
	python3.9 tools/finbotdb --database ${FINBOT_DB_URL} destroy && \
	python3.9 tools/finbotdb --database ${FINBOT_DB_URL} build

finbotdb-hydrate:
	python3.9 tools/finbotdb --database ${FINBOT_DB_URL} hydrate \
		--data-file ./tools/hydrate.json

finbotdb-add-account:
	python3.9 tools/finbotdb --database ${FINBOT_DB_URL} add-account \
		--secret ${FINBOT_SECRET_PATH} \
		--account ${FINBOT_ACCOUNT_PATH}

finbotdb-dump-account:
	python3.9 tools/finbotdb --database ${FINBOT_DB_URL} dump-account \
		--secret ${FINBOT_SECRET_PATH} \
		--account-id ${account_id}

finbotdb-psql:
	env PGPASSWORD=${FINBOT_DB_PASSWORD} \
		psql -h ${FINBOT_DB_HOSTNAME} -U ${FINBOT_DB_USER} -d ${FINBOT_DB_DBNAME}

finbot-wait:
	tools/finbot-wait

init-dev:
	tools/init-dev.sh

docker-dev:
	docker exec -it dev /bin/bash
