run-finbotwsrv-dev:
	env FLASK_APP=./finbot/apps/finbotwsrv/finbotwsrv.py \
		FLASK_ENV=development \
		flask run --port 5001 -h 0.0.0.0

run-snapwsrv-dev:
	env FLASK_APP=./finbot/apps/snapwsrv/snapwsrv.py \
		FLASK_ENV=development \
		SECRET_PATH=$(shell pwd)/.secure/secret.txt \
		ACCOUNTS_PATH=$(shell pwd)/.secure/accounts \
		flask run --port 5000 -h 0.0.0.0

run-tester-dev:
	env python3.7 -m finbot.apps.tester.tester \
			--currency EUR \
			--dump-balances --dump-assets \
			--secret-file $(shell pwd)/.secure/secret.txt \
			--accounts-file $(shell pwd)/.secure/accounts \
			--show-browser \
			--pause-on-error \
			--no-threadpool \
			${TESTER_ACCOUNTS}

run-tester:
	env python3.7 -m finbot.apps.tester.tester \
			--currency EUR \
			--secret-file $(shell pwd)/.secure/secret.txt \
			--accounts-file $(shell pwd)/.secure/accounts \
			${TESTER_ACCOUNTS}

reveal-accounts:
	env PYTHONPATH=$(shell pwd):${PYTHONPATH} python3.7 tools/crypt \
		fernet-decrypt \
		-k $(shell pwd)/.secure/secret.txt \
		-i $(shell pwd)/.secure/accounts | less

edit-accounts:
	env PYTHONPATH=$(shell pwd):${PYTHONPATH} \
	python3.7 tools/crypt \
		fernet-decrypt \
		-k $(shell pwd)/.secure/secret.txt \
		-i $(shell pwd)/.secure/accounts > .accounts.tmp && \
	chmod 600 .accounts.tmp && \
	vim .accounts.tmp && \
	python3.7 tools/crypt \
		fernet-encrypt \
		-k $(shell pwd)/.secure/secret.txt \
		-i .accounts.tmp > $(shell pwd)/.secure/accounts && \
	rm .accounts.tmp
