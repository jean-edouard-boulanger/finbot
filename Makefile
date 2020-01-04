export PYTHONPATH := $(PYTHONPATH):$(shell pwd)
$(info PYTHONPATH=${PYTHONPATH})

export FINBOT_SECRET_PATH := $(if $(FINBOT_SECRET_PATH),$(FINBOT_SECRET_PATH),.secure/secret.txt)
$(info FINBOT_SECRET_PATH=${FINBOT_SECRET_PATH})

export FINBOT_ACCOUNTS_PATH := $(if $(FINBOT_ACCOUNTS_PATH),$(FINBOT_ACCOUNTS_PATH),.secure/accounts)
$(info FINBOT_ACCOUNTS_PATH=${FINBOT_ACCOUNTS_PATH})

export FINBOT_DB_HOSTNAME := $(if $(FINBOT_DB_HOSTNAME),$(FINBOT_DB_HOSTNAME),127.0.0.1)
$(info FINBOT_DB_HOSTNAME=${FINBOT_DB_HOSTNAME})

export FINBOT_DB_USER := $(if $(FINBOT_DB_USER),$(FINBOT_DB_USER),finbot)
$(info FINBOT_DB_USER=${FINBOT_DB_USER})

export FINBOT_DB_PASSWORD := $(if $(FINBOT_DB_PASSWORD),$(FINBOT_DB_PASSWORD),finbot)
$(info FINBOT_DB_PASSWORD=${FINBOT_DB_PASSWORD})

export FINBOT_DB_DBNAME := $(if $(FINBOT_DB_DBNAME),$(FINBOT_DB_DBNAME),finbot)
$(info FINBOT_DB_DBNAME=${FINBOT_DB_DBNAME})

export FINBOT_DB_URL := postgresql+psycopg2://${FINBOT_DB_USER}:${FINBOT_DB_PASSWORD}@${FINBOT_DB_HOSTNAME}/${FINBOT_DB_DBNAME}
$(info FINBOT_DB_URL=${FINBOT_DB_URL})

export FINBOT_SNAP_ENDPOINT := $(if $(FINBOT_SNAP_ENDPOINT),$(FINBOT_SNAP_ENDPOINT),http://127.0.0.1:5000)
$(info FINBOT_SNAP_ENDPOINT=${FINBOT_SNAP_ENDPOINT})

export FINBOT_CCY := $(if $(FINBOT_CCY),$(FINBOT_CCY),EUR)
$(info FINBOT_CCY=${FINBOT_CCY})


info:
	$(info END)

run-finbotwsrv-dev:
	env FLASK_APP=./finbot/apps/finbotwsrv/finbotwsrv.py \
		FLASK_ENV=development \
		flask run \
			--port 5001 \
			--extra-files 'finbot/providers/*.py' \
			-h 0.0.0.0

run-snapwsrv-dev:
	env FLASK_APP=./finbot/apps/snapwsrv/snapwsrv.py \
		FLASK_ENV=development \
		flask run \
			--port 5000 \
			-h 0.0.0.0

build-finbotwsrv-docker:
	docker build -t finbot/finbotwsrv:latest -f finbotwsrv.Dockerfile .

build-providers-tester-docker: build-finbotwsrv-docker
	docker build -t finbot/providers-tester:latest -f tester.Dockerfile .

test-providers-docker:
	docker run \
		-v $(shell pwd):/finbot \
		--workdir /finbot \
		--env PYTHONPATH='${PYTONPATH}:/finbot' \
		--rm -it \
		finbot/providers-tester:latest \
		tools/providers-tester \
			--currency ${FINBOT_CCY} \
			--dump-balances --dump-assets \
			--secret-file ${FINBOT_SECRET_PATH} \
			--accounts-file ${FINBOT_ACCOUNTS_PATH} \
			${TESTER_ACCOUNTS}

test-providers-debug:
	tools/providers-tester \
			--currency ${FINBOT_CCY} \
			--dump-balances --dump-assets \
			--secret-file ${FINBOT_SECRET_PATH} \
			--accounts-file ${FINBOT_ACCOUNTS_PATH} \
			--show-browser \
			--pause-on-error \
			--no-threadpool \
			${TESTER_ACCOUNTS}

test-providers:
	tools/providers-tester \
			--currency ${FINBOT_CCY} \
			--secret-file ${FINBOT_SECRET_PATH} \
			--accounts-file ${FINBOT_ACCOUNTS_PATH} \
			${TESTER_ACCOUNTS}

test-snapwsrv:
	tools/snapwsrv-tester \
		--endpoint ${FINBOT_SNAP_ENDPOINT} \
		--account-id ${ACCOUNT_ID}

confirm-override-accounts:
	[[ ! -d .secure ]] || tools/yes_no 'This will erase existing accounts, continue?'

init-accounts: confirm-override-accounts
	mkdir -p .secure && \
	tools/crypt fernet-key > ${FINBOT_SECRET_PATH} && \
	chmod 600 ${FINBOT_SECRET_PATH} && \
	cp tools/accounts.tpl.json .accounts.tmp && \
	tools/crypt fernet-encrypt \
		-k ${FINBOT_SECRET_PATH} \
		-i .accounts.tmp > ${FINBOT_ACCOUNTS_PATH} && \
	rm .accounts.tmp && \
	chmod 600 ${FINBOT_ACCOUNTS_PATH}

show-accounts:
	tools/crypt fernet-decrypt \
		-k ${FINBOT_SECRET_PATH} \
		-i ${FINBOT_ACCOUNTS_PATH} | less

edit-accounts:
	tools/crypt fernet-decrypt \
		-k ${FINBOT_SECRET_PATH} \
		-i ${FINBOT_ACCOUNTS_PATH} > .accounts.tmp.json && \
	chmod 600 .accounts.tmp.json && \
	vim .accounts.tmp.json && \
	tools/crypt \
		fernet-encrypt \
		-k ${FINBOT_SECRET_PATH} \
		-i .accounts.tmp.json > ${FINBOT_ACCOUNTS_PATH} && \
	rm .accounts.tmp.json

finbotdb-build:
	tools/finbotdb build

finbotdb-destroy:
	tools/finbotdb destroy

finbotdb-rebuild:
	tools/finbotdb destroy && tools/finbotdb build

finbotdb-hydrate:
	tools/finbotdb hydrate \
		--secret ${FINBOT_SECRET_PATH} \
		--accounts ${FINBOT_ACCOUNTS_PATH}

finbotdb-psql:
	env PGPASSWORD=finbot psql -h 127.0.0.1 -U finbot -d finbot

