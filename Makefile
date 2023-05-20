export FINBOT_EDIT_CMD ?= code --wait
export BLACK_SETTINGS = --exclude 'migrations/|webapp/|venv/' .
export ISORT_SETTINGS = --profile black finbot/ tools/
export PYTHONPATH := ${PWD}:${PYTHONPATH}

alembic-gen:
	tools/check-env.sh message;
	alembic revision --autogenerate -m "${message}"

alembic-upgrade:
	alembic upgrade head

alembic-downgrade:
	alembic downgrade -1

alembic-history:
	alembic history

pip-compile-all:
	./tools/pip-compile-all

docker-build-webapp:
	cd webapp && docker build -t finbotapp/webapp:latest -f Dockerfile --pull .

docker-build-runtime:
	docker build --target runtime -t finbotapp/runtime:latest -f Dockerfile --pull .

docker-build-runtime-playwright:
	docker build --target runtime-playwright -t finbotapp/runtime-playwright:latest -f Dockerfile --pull .

docker-build-runtime-dev:
	docker build --target runtime-dev -t finbotapp/runtime-dev:latest -f Dockerfile --pull .

docker-build-prod: docker-build-runtime docker-build-runtime-playwright docker-build-webapp
docker-build-dev: docker-build-runtime-dev
docker-build-all: docker-build-dev docker-build-prod

trigger-valuation:
	tools/check-env.sh accounts;
	docker-compose exec schedsrv \
		./tools/run -- python3.11 finbot/apps/schedsrv/schedsrv.py \
			--mode one_shot \
			--accounts ${accounts}

run-system-tests:
	docker-compose run --rm operator env FINBOT_WAIT_DEPS=appwsrv,finbotwsrv ./tools/finbot-wait;
	docker-compose run --rm operator python3.11 -m pytest tests/system/

finbotdb-build:
	python3.11 tools/finbotdb build

finbotdb-destroy:
	python3.11 tools/finbotdb destroy

finbotdb-rebuild:
	python3.11 tools/finbotdb destroy && \
	python3.11 tools/finbotdb build

finbotdb-hydrate:
	python3.11 tools/finbotdb hydrate \
		--data-file ./tools/hydrate.json

finbotdb-add-account:
	tools/check-env.sh FINBOT_SECRET_PATH;
	tools/check-env.sh FINBOT_ACCOUNT_PATH;
	python3.11 tools/finbotdb add-account \
		--secret ${FINBOT_SECRET_PATH} \
		--account ${FINBOT_ACCOUNT_PATH}

finbotdb-dump-account:
	tools/check-env.sh FINBOT_SECRET_PATH;
	tools/check-env.sh FINBOT_ACCOUNT_PATH;
	python3.11 tools/finbotdb dump-account \
		--secret ${FINBOT_SECRET_PATH} \
		--account-id ${account_id}

finbotdb-psql:
	tools/check-env.sh FINBOT_DB_PASSWORD;
	tools/check-env.sh FINBOT_DB_HOSTNAME;
	tools/check-env.sh FINBOT_DB_USER;
	tools/check-env.sh FINBOT_DB_DBNAME;
	env PGPASSWORD=${FINBOT_DB_PASSWORD} \
		psql -h ${FINBOT_DB_HOSTNAME} -U ${FINBOT_DB_USER} -d ${FINBOT_DB_DBNAME}

init-dev:
	tools/init-dev.sh

py-unit-tests:
	python3.11 -m pytest tests/unit_tests

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
	flake8 --exclude migrations/,venv/,webapp/ --max-line-length 120

version-bump-check:
	tools/versioning check-version-bump

black-check:
	black --check $(BLACK_SETTINGS)

black:
	black $(BLACK_SETTINGS)

isort-check:
	isort --check $(ISORT_SETTINGS)

isort:
	isort $(ISORT_SETTINGS)

mypy:
	mypy --strict finbot/

unit-tests-py:
	python3.11 -m pytest -vv tests/unit

unit-tests: unit-tests-py

banned-keywords-check-py:
	tools/banned-keywords.py --source-dirs finbot

lint-sh:
	grep -rl '^#!/.*bash' --exclude-dir=webapp --exclude-dir='./.*' . |\
 		xargs shellcheck -e SC1090 -e SC1091 -e SC2002 -S style

lint-py: mypy flake8 black-check isort-check banned-keywords-check-py unit-tests-py
lint-ts: eslint tsc-build-check prettier-check-ts banned-keywords-check-ts
lint-all: version-bump-check lint-py lint-ts lint-sh

format-py: black isort
format-ts: prettier-ts
format-all: format-py format-ts
