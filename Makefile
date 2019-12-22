export PYTHONPATH := $(PYTHONPATH):$(shell pwd)

run-finbotwsrv-dev:
	env FLASK_APP=./finbot/apps/finbotwsrv/finbotwsrv.py \
		FLASK_ENV=development \
		flask run --port 5001 -h 0.0.0.0

run-snapwsrv-dev:
	env FLASK_APP=./finbot/apps/snapwsrv/snapwsrv.py \
		FLASK_ENV=development \
		SECRET_PATH=.secure/secret.txt \
		ACCOUNTS_PATH=.secure/accounts \
		flask run --port 5000 -h 0.0.0.0

run-tester-dev:
	env python3.7 -m finbot.apps.tester.tester \
			--currency EUR \
			--dump-balances --dump-assets \
			--secret-file .secure/secret.txt \
			--accounts-file .secure/accounts \
			--show-browser \
			--pause-on-error \
			--no-threadpool \
			${TESTER_ACCOUNTS}

run-tester:
	env python3.7 -m finbot.apps.tester.tester \
			--currency EUR \
			--secret-file .secure/secret.txt \
			--accounts-file .secure/accounts \
			${TESTER_ACCOUNTS}

confirm-override-accounts:
	[[ ! -d .secure ]] || tools/yes_no 'This will erase existing accounts, continue?'

init-accounts: confirm-override-accounts
	mkdir -p .secure && \
	tools/crypt fernet-key > .secure/secret.txt && \
	chmod 600 .secure/secret.txt && \
	cp tools/accounts.tpl.json .accounts.tmp && \
	tools/crypt fernet-encrypt \
		-k .secure/secret.txt \
		-i .accounts.tmp > .secure/accounts && \
	rm .accounts.tmp && \
	chmod 600 .secure/accounts

show-accounts:
	tools/crypt fernet-decrypt \
		-k .secure/secret.txt \
		-i .secure/accounts | less

edit-accounts:
	tools/crypt fernet-decrypt \
		-k .secure/secret.txt \
		-i .secure/accounts > .accounts.tmp && \
	chmod 600 .accounts.tmp && \
	vim .accounts.tmp && \
	tools/crypt \
		fernet-encrypt \
		-k .secure/secret.txt \
		-i .accounts.tmp > .secure/accounts && \
	rm .accounts.tmp
